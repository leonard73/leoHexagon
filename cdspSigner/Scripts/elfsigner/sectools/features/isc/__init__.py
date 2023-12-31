# ===============================================================================
#
#  Copyright (c) 2013-2017 Qualcomm Technologies, Inc.
#  All Rights Reserved.
#  Confidential and Proprietary - Qualcomm Technologies, Inc.
#
# ===============================================================================
"""
:Authors: sectools

Main interface to the secimage functionalities. Supports APIs for
command line interface, UI interface and test interface.
"""

import __secfile__
__secfile__.init()

import os
import sys
import traceback

from __secfile__ import DIR_PATH
from sectools.common.utils import c_path
from sectools.common.utils.c_logging import logger
from sectools.common.utils.c_misc import store_data_to_file, load_data_from_file, PROGRESS_CB_PYPASS, ProgressNotifier, multi_image_string
from sectools.common.parsegen.elf.segment.type import PT_LOAD
from sectools.features.isc.parsegen.elf import NON_ENCRYPT_SEGMENT_OS_TYPE
from sectools.features.isc import defines, stager
from sectools.features.isc.cfgparser import ConfigDir, ConfigParser
from sectools.features.isc.encryption_service import get_encdec
from sectools.features.isc.encryption_service.base import encdec as encdec_base
from sectools.features.isc.encryption_service.unified import encrypted_key_provider_id_supported
from sectools.features.isc.secpolicy import create_security_policy_list

PROGRESS_TOTAL_STAGES = 7

PARSEGEN_PATH = c_path.join(DIR_PATH, 'parsegen', 'config', 'parsegen_config.xml')


class SecImageCore(object):
    """Provides interface for user to set up parameters (including input files,
    output directory, etc) and perform various operations (signing, encryption).


    User can select the config file using:

    - :meth:`chipset`
    - :meth:`config_path`

    User can specify images for processing using:

    - :meth:`set_image_path`
    - :meth:`set_meta_build_path`

    User can specify output using:

    - :meth:`output_dir`
    - :meth:`mini_build_path`

    User can finally perform the following operations:

    - :meth:`verify_inputs`
    - :meth:`sign`
    - :meth:`encrypt`
    - :meth:`validate`

    User can also perform multiple operations using :meth:`process`

    :param str config_dir: Path to the directory containing the config files
        for the supported chipsets.
    :param bool debug: If all the underlying modules should work in debug mode
        (save debug logs, etc).

    .. data:: debug

        (bool) Is debug mode enabled. The debug logs will be stored in :meth:`output_dir`

    """

    def __init__(self, config_dir=defines.DEFAULT_CONFIG_DIR, debug=False):
        # Initialize the internal properties
        self._config_dir_obj = ConfigDir(config_dir)
        self._img_config_parser = None
        self._parsegen_config = None
        self._stager = None
        self._authority = defines.AUTHORITY_OEM

        # Generate Parsegen_config from parsegen_config.xml
        from sectools.features.isc.parsegen.config.parser import ParsegenCfgParser
        self._parsegen_config = ParsegenCfgParser(PARSEGEN_PATH)

        # Initialize the public properties
        self.debug = debug

    @property
    def config_dir(self):
        """(str) Path to the config directory provided in params. The config_dir
        path cannot be set directly.
        """
        return self._config_dir_obj.config_dir

    @config_dir.setter
    def config_dir(self, config_dir):
        raise RuntimeError('Config dir cannot be set.')

    @property
    def available_chipsets(self):
        """(list[str]) A list of chipsets for which config files are available
        in the :meth:`config_dir`. The list of available chipsets cannot be set
        directly.
        """
        return self._config_dir_obj.chipsets

    @available_chipsets.setter
    def available_chipsets(self, chipset_list):
        raise RuntimeError('Available chipsets cannot be set.')

    @property
    def chipset(self):
        """(str) Chipset that is selected for the current run. The chipset
        selection will update the :meth:`config_path`
        """
        if self._img_config_parser is not None:
            return self._img_config_parser.chipset
        else:
            raise RuntimeError('Chipset Path is not set.')

    @chipset.setter
    def chipset(self, chipset):
        self.set_chipset(chipset)

    def set_chipset(self, chipset, overrides=None, spec_overrides=None):
        # Log if the chipset is changed
        try:
            selected_chipset = self.chipset
            if selected_chipset:
                logger.note('Switching chipset from "' + selected_chipset + '" to "' + chipset + '"')
        except Exception:
            pass

        # Update the config path based on the given chipset
        config_path = self._config_dir_obj.get_chipset_config_path(chipset)
        if config_path is None:
            raise RuntimeError('Config file is not found for chipset: ' + str(chipset))
        self.set_config_path(config_path, overrides, spec_overrides)
        logger.info('Chipset is set to: ' + chipset)

    @property
    def config_path(self):
        """(str) Config path that is selected for the current run. The
        config_path selection will update the :meth:`chipset`
        """
        if self._img_config_parser is not None:
            return self._img_config_parser.config_path
        else:
            raise RuntimeError('Config Path is not set.')

    @config_path.setter
    def config_path(self, config_path):
        self.set_config_path(config_path)

    def set_config_path(self, config_path, overrides=None, spec_overrides=None):
        # Log if the config_path is changed
        try:
            selected_config_path = self.config_path
            if selected_config_path:
                logger.note('Switching config_path: ' + '\n'
                            '    ' + 'from: ' + selected_config_path + '\n'
                            '    ' + ' to: ' + config_path)
        except Exception:
            pass

        # Update the config_path
        self._img_config_parser = ConfigParser(config_path, overrides, spec_overrides)
        logger.info('Config path is set to: ' + config_path)

        # Reset the stager at this point
        if self._stager is not None:
            logger.note('Resetting image list due to config path change.')
            self._stager = None

    @property
    def authority(self):
        """(str) Config path that is selected for the current run. The
        config_path selection will update the :meth:`chipset`
        """
        return self._authority

    @authority.setter
    def authority(self, authority):
        if authority not in defines.AUTHORITIES_SUPPORTED:
            raise RuntimeError('Unknown authority for secure operations: ' + str(authority))
        self._authority = authority

    @property
    def available_sign_ids(self):
        """(list[str]) A list of sign_ids available from the selected
        :meth:`config_path`/:meth:`chipset`.
        """
        if self._img_config_parser is not None:
            return self._img_config_parser.sign_id_list
        else:
            raise RuntimeError('Set chipset or config Path before querying the available sign ids.')

    @available_sign_ids.setter
    def available_sign_ids(self, chipset_list):
        raise RuntimeError('Available sign ids cannot be set.')

    def set_image_path(self, image_path, sign_id, gen_multi_image=False, multi_image_path=None):
        """Sets the image that will be processed.

        :param str image_path: Path to the image to be processed
        :param str sign_id: sign_id corresponding to the image_path. This must
            be one of the :meth:`available_sign_ids`
        :param bool gen_multi_image: Determines whether a new Multi-Image Sign & Integrity image will be generated & operated on
        :param str multi_image_path: Path to the existing Multi-Image Sign & Integrity image to be operated on
        """
        if self._img_config_parser is not None and self._parsegen_config is not None:
            self._stager = stager.ImagePathsStager(image_path, self._img_config_parser, self._parsegen_config, self.authority, sign_id, gen_multi_image, multi_image_path)
        else:
            raise RuntimeError('Set chipset or config Path before setting the image path.')

    def set_meta_build_path(self, meta_build_path, sign_id_list=[], gen_multi_image=False):
        """Sets the meta build path from which the images to be processed will
        be queried.

        :param str meta_build_path: Path to the meta build.
        :param bool gen_multi_image: Determines whether a new Multi-Image Sign & Integrity image will be generated & operated on
        """
        if self.meta_supports_sign_id(meta_build_path):
            self._stager = stager.MetaBuildStager(meta_build_path, self._config_dir_obj, self._parsegen_config, self.authority, sign_id_list, gen_multi_image)
        else:
            self._stager = stager.MetaBuildTmpStager(meta_build_path, self._config_dir_obj, self._img_config_parser, self._parsegen_config, self.authority, sign_id_list, gen_multi_image)

    @property
    def image_path_list(self):
        """(list[str]) List of source image paths that are being operated on.
        This is updated once one of :meth:`set_image_path`,
        :meth:`set_meta_build_path` is used to specify the images to be
        processed.
        """
        if self._stager is not None:
            return self._stager.image_path_list
        else:
            raise RuntimeError('Image list is not set. '
                               'Set one of image_path or meta_build_path.')

    @image_path_list.setter
    def image_path_list(self, image_path_list):
        raise RuntimeError('Image path list cannot be set directly. '
                           'Use set_image_path or set_meta_build to set the image paths.')

    @property
    def image_info_list(self):
        """(list[ImageInfo]) A list of :class:`imageinfo.ImageInfo` objects that are being
        operated on.
        """
        if self._stager is not None:
            return self._stager.image_info_list
        else:
            raise RuntimeError('Image Info list is not set. '
                               'Set one of image_path or meta_build_path.')

    @image_info_list.setter
    def image_info_list(self, image_info_list):
        raise RuntimeError('Image Info list cannot be set directly.')

    @property
    def multi_image_imageinfo_dict(self):
        """A dictionary that maps :class:`str` chipsets to objects of type :class:`imageinfo.ImageInfo` that correspond to the
        Multi-Image Sign & Integrity image to be operated on for the corresponding chipset.
        """
        if self._stager is not None:
            return self._stager.multi_image_imageinfo_dict
        else:
            raise RuntimeError(multi_image_string() + ' Image Info is not set. '
                               'Set one of image_path or meta_build_path.')

    @property
    def output_dir(self):
        """(str) Path to the output directory to use for saving the logs, output
        files.
        """
        if self._stager is not None:
            return self._stager.output_dir
        else:
            raise RuntimeError('Image list is not set. '
                               'Set one of image_path or meta_build_path. '
                               'Then retry setting output directory.')

    @output_dir.setter
    def output_dir(self, output_dir):
        # Log if the output_dir is changed
        try:
            selected_output_dir = self.output_dir
            if selected_output_dir:
                logger.note('Switching output_dir: ' + '\n'
                            '    ' + 'from: ' + selected_output_dir + '\n'
                            '    ' + ' to: ' + output_dir)
        except Exception:
            pass

        # Update the output_dir
        self._stager.output_dir = output_dir
        logger.info('Output dir is set to: ' + output_dir)

        # Clear the minimized build setting
        try:
            self._stager.mini_build_path = ''
        except Exception:
            pass

    @property
    def mini_build_path(self):
        """(str) Path to the minimized build directory to use for saving the
        logs, output files.
        """
        if self._stager is not None:
            return self._stager.mini_build_path
        else:
            raise RuntimeError('Image list is not set. '
                               'Set one of image_path or meta_build_path. '
                               'Then retry querying/setting minimized build.')

    @mini_build_path.setter
    def mini_build_path(self, mini_build_path):
        # Log if the mini_build_path is changed
        selected_mini_build_path = self.mini_build_path
        if selected_mini_build_path:
            logger.note('Switching mini_build_path: ' + '\n'
                        '    ' + 'from: ' + selected_mini_build_path + '\n'
                        '    ' + ' to: ' + mini_build_path)

        # Update the mini_build_path
        self._stager.mini_build_path = mini_build_path
        logger.info('Minimized Build is set to: ' + mini_build_path)

        # Clear the output dir setting
        try:
            self._stager.output_dir = ''
        except Exception:
            pass

    @classmethod
    def meta_supports_sign_id(self, meta_build_path):
        return stager.meta_build_stager.MetaBuildStager.meta_supports_sign_id(meta_build_path)

    # Helper method to override prefix of debug dumped files for images with multiple security policies
    @staticmethod
    def _get_prefix_override(existing_prefix, file_type):
        if existing_prefix is None:
            return file_type + "_wrapped"
        else:
            return existing_prefix + file_type + "_wrapped"

    def process(self,
                verify_setup=False,
                sign_attr=False,
                integrity_check=False,
                sign=False,
                encrypt=False,
                decrypt=False,
                no_op=False,
                val_image=False,
                val_integrity_check=False,
                val_sign=False,
                val_encrypt=False,
                m_sign_attr=False,
                m_integrity_check=False,
                m_sign=False,
                m_encrypt=False,
                m_decrypt=False,
                m_val_image=False,
                m_val_integrity_check=False,
                m_val_sign=False,
                m_val_encrypt=False,
                gen_multi_image=False,
                root_cert_hash=None,
                progress_cb=PROGRESS_CB_PYPASS,
                ):
        """Performs the secure-image related operations specified from the params.

        :param bool verify_setup: Verify that the configuration of the object is correct and return. This will ignore any other params.
        :param bool sign_attr: Add signing attributes to hash segment of images.
        :param bool integrity_check: Add integrity check to the image.
        :param bool sign: Sign the images. (Re-sign if image is already signed)
        :param bool encrypt: Encrypt the images. (Re-encrypt if image is already encrypted)
        :param bool no_op: Perform no operation on the images when adding their entries to the Multi-Image Sign & Integrity image.
        :param bool val_image: Validate the integrity of the image against the config file.
        :param bool val_integrity_check: Validate the integrity check in the image.
        :param bool val_sign: Validate that the image is signed and validate the integrity of the signing related data.
        :param bool val_encrypt: Validate that the image is encrypted and validate the integrity of the encryption related data.
        :param bool m_sign_attr: Add signing attributes to hash segment of the Multi-Image Sign & Integrity image.
        :param bool m_integrity_check: Add integrity check to the Multi-Image Sign & Integrity image.
        :param bool m_sign: Sign the Multi-Image Sign & Integrity image. (Re-sign if image is already signed)
        :param bool m_encrypt: Encrypt the Multi-Image Sign & Integrity image. (Re-encrypt if image is already encrypted)
        :param bool m_val_image: Validate the integrity of the Multi-Image Sign & Integrity image against the config file.
        :param bool m_val_integrity_check: Validate the integrity check in the Multi-Image Sign & Integrity image.
        :param bool m_val_sign: Validate that the Multi-Image Sign & Integrity image is signed and validate the integrity of the signing related data.
        :param bool m_val_encrypt: Validate that the Multi-Image Sign & Integrity image is encrypted and validate the integrity of the encryption related data.
        :param bool gen_multi_image: Perform multi-image sign and integrity operations.
        :param cb progress_cb: Callback method to get a status update during processing.

            Callback method should have this format:
            ::
                def progress_cb(status_string, progress_percent):
                    \"""
                    :param str status_string: the current status.
                    :param int progress_percent: the progress (in percent)
                    \"""
                    ...


        """
        from imageinfo import ImageInfo, StatusInfo
        from sectools.features.isc.signer.remote import RemoteSignerNote

        # Ensure that one or more image files is provided for processing
        if self._stager is None or not self.image_path_list:
            raise RuntimeError('Please specify one or more images for processing')

        # Ensure the correct set of operations is provided
        if not (verify_setup or integrity_check or sign or encrypt or decrypt or no_op or val_image or val_integrity_check or val_sign or val_encrypt):
            raise RuntimeError('Please specify one or more operations to perform.')

        # Ensure the correct Multi-Image set of operations is provided
        if self.multi_image_imageinfo_dict and not (m_integrity_check or m_sign or m_encrypt or m_decrypt or m_val_image or m_val_integrity_check or m_val_sign or m_val_encrypt):
            raise RuntimeError('Please specify one or more ' + multi_image_string() + ' operations to perform.')

        # Print the openssl path
        version = ''
        path_info = 'is unavailable. Please run "which openssl" and "openssl version" to check openssl version info, and upgrade to required version'
        try:
            from sectools.common import crypto
            version = 'v' + '.'.join(tuple(str(x) for x in crypto.openssl.OPENSSL_VERSION_MIN)) + ' or greater '
            path_info = 'is available at: "' + crypto.discovery_factory.get_impl(crypto.modules.MOD_OPENSSL) + '"'
        except Exception as e:
            pass
        logger.info('Openssl ' + version + path_info)

        if verify_setup:
            logger.note('The inputs provided (config, cmd args) are valid.')
            return

        # Start processing images
        individual_image_count = len(self.image_info_list)
        total_image_count = individual_image_count
        if self.multi_image_imageinfo_dict:
            total_image_count += len(self.multi_image_imageinfo_dict)
        progress = ProgressNotifier(total_image_count, progress_cb, PROGRESS_TOTAL_STAGES)

        # If Multi-Image operations need to be performed, save parsegens of individual images for each target
        parsegens = dict()

        def _process(idx, image, sign_attr, integrity_check, sign, encrypt, decrypt, no_op, val_image, val_integrity_check, val_sign, val_encrypt, gen_multi_image=False, is_multi_image=False, save_parsegen=False):
            assert isinstance(image, ImageInfo)

            logger.info('------------------------------------------------------')
            if not is_multi_image:
                status_string = ('Processing ' + str(idx + 1) + '/' + str(total_image_count) + ': ' + image.image_under_operation)
            else:
                # Creating a new Multi-Image image
                if gen_multi_image:
                    status_prefix = 'Creating & Processing '
                    status_suffix = ': ' + image.image_under_operation
                # Modifying an existing Multi-Image image
                else:
                    status_prefix = 'Processing '
                    status_suffix = ' (' + multi_image_string() + ' image): ' + image.image_under_operation
                status_string = (status_prefix + str(idx + 1) + '/' + str(total_image_count) + status_suffix)
            logger.info(status_string + '\n')

            # Send a progress notification to the toplevel
            progress.status = status_string
            progress.cur = idx
            progress.cur_stage = 0

            file_logger_id = None
            image.authority = self.authority

            try:
                # Create the required directory structure for this image
                image_output_dir = image.dest_image.image_dir
                try:
                    c_path.create_dir(image_output_dir)
                except Exception as e:
                    raise RuntimeError('Could not create output directory: ' + image_output_dir + '\n'
                                                                                                  '    ' + 'Error: ' + str(e))

                # Enable/Disable debug
                image.dest_image.debug_enable = self.debug
                c_path.create_debug_dir(image.dest_image.debug_dir)

                # Set the root cert hash
                image.validation_root_cert_hash = root_cert_hash

                # Enable file logging to the directory
                file_logger_id = logger.add_file_logger(c_path.join(image_output_dir, 'SecImage_log.txt'), logger.verbosity)

                # Create the security policies list for this image
                security_policy_list = create_security_policy_list(image)

                # Parsegen object
                parsegen = None

                # For secure operations
                if integrity_check or sign or encrypt or decrypt:
                    parsegen = self._process_secure_operation(image, progress, security_policy_list, sign_attr, integrity_check, sign, encrypt, decrypt, gen_multi_image=gen_multi_image, parsegens=parsegens.get(image.chipset, list()))

                # For validation
                if val_image or val_integrity_check or val_sign or val_encrypt:
                    # Bypass validation when encrypted key provide is configured as UIE server because decryption will always fail
                    if parsegen is not None and parsegen.is_encrypted() and encrypted_key_provider_id_supported(image.general_properties.UIE_key):
                        logger.warning("Skipping validation because encrypted key provider is configured as UIE server")
                    else:
                        parsegen = self._process_validation(image, progress, security_policy_list, val_image, val_integrity_check, val_sign, val_encrypt)

                # For no-op
                if no_op:
                    parsegen = self._create_parsegen(image, progress, security_policy_list)

                # Print the image data
                if parsegen is not None:
                    logger.info('\n' + str(parsegen))
                    # Save parsegen for multi_image operations
                    if save_parsegen:
                        if parsegen.supports_multi_image():
                            if image.chipset in parsegens:
                                parsegens[image.chipset].append(parsegen)
                            else:
                                parsegens[image.chipset] = [parsegen]
                        else:
                            raise RuntimeError(multi_image_not_supported_error_message.format(image.image_under_operation))

                # Set overall processing to true
                if not ((val_image and image.status.validate_parsegen.state == StatusInfo.ERROR) or
                        (val_integrity_check and image.status.validate_integrity_check.state == StatusInfo.ERROR) or
                        (val_sign and image.status.validate_sign.state == StatusInfo.ERROR) or
                        (val_encrypt and image.status.validate_encrypt.state == StatusInfo.ERROR)):
                    image.status.overall.state = StatusInfo.SUCCESS

            except RemoteSignerNote as e:
                logger.info('NOTE: ' + str(e), color=logger.YELLOW)
                # Image operation failed for individual image that was to be added to Multi-Image Signing & Integrity image
                if save_parsegen:
                    logger.error(adding_image_error_message.format(image.image_under_operation))
            except Exception:
                logger.error(traceback.format_exc())
                logger.error(sys.exc_info()[1])
                # Image operation failed for individual image that was to be added to Multi-Image Signing & Integrity image
                if save_parsegen:
                    logger.error(adding_image_error_message.format(image.image_under_operation))
            finally:
                if file_logger_id is not None:
                    logger.removeFileLogger(file_logger_id)

            logger.info('------------------------------------------------------\n')

        adding_image_error_message = "Image operation failed for image {0}\n\t" + multi_image_string() + " image won't contain entries for failed images."
        multi_image_not_supported_error_message = "Image {0} does not support being added to " + multi_image_string() + " image."

        for idx, image in enumerate(self.image_info_list):
            _process(idx, image, sign_attr, integrity_check, sign, encrypt, decrypt, no_op, val_image, val_integrity_check, val_sign, val_encrypt, save_parsegen=True if self.multi_image_imageinfo_dict else False)

        # Handle multi-image operations
        if self.multi_image_imageinfo_dict:
            image_index = 0
            for target, imageinfo in self.multi_image_imageinfo_dict.iteritems():
                _process(individual_image_count+image_index, imageinfo, m_sign_attr, m_integrity_check, m_sign, m_encrypt, m_decrypt, no_op, m_val_image, m_val_integrity_check, m_val_sign, m_val_encrypt, gen_multi_image=gen_multi_image, is_multi_image=True)
                image_index += 1

        progress.complete()

    def _process_secure_operation(self, image, progress, security_policy_list,
                                  sign_attr, i_integrity_check, i_sign, i_encrypt, i_decrypt, idx=0, prefix_override=None, gen_multi_image=False, parsegens=None):
        from imageinfo import ImageInfo, StatusInfo
        # Check bounds
        if len(security_policy_list) == 0:
            raise RuntimeError('Security policy list must not be empty.')
        elif len(security_policy_list) <= idx:
            raise RuntimeError('Security policy list length must be more than index.')

        # Get the current security policy
        file_type = security_policy_list[idx].file_type
        integrity_check = security_policy_list[idx].integrity_check and i_integrity_check
        sign = security_policy_list[idx].sign and i_sign
        encrypt = security_policy_list[idx].encrypt and i_encrypt
        decrypt = security_policy_list[idx].encrypt and i_decrypt

        # Create the encryptor object
        encdec = None
        if image.general_properties.selected_encryptor:
            c_path.create_debug_dir(image.dest_image.debug_dir_encdec)
            encdec = get_encdec(image, False)

        # Create the parsegen object
        file_type_backup = image.image_type.file_type
        encdec_backup = image.encdec
        image.image_type.file_type = file_type
        image.encdec = encdec
        try:
            parsegen = self._status_updater(self._create_parsegen_obj,
                                            image.status.parsegen,
                                            progress,
                                            True,
                                            image,
                                            False,
                                            sign,
                                            prefix_override,
                                            not gen_multi_image,
                                            parsegens,
                                            sign_attr)
        finally:
            image.image_type.file_type = file_type_backup
            image.encdec = encdec_backup

        # Validate the authority settings
        self.validate_authority_settings(self.authority,
                                         image.general_properties.secboot_version,
                                         image.general_properties.qti_sign,
                                         image.general_properties.oem_sign,
                                         image.general_properties.num_root_certs,
                                         encrypt)

        # Do not allow signed unencrypted elf images to be encrypted as the
        # Sign will not longer match the encrypted image's tosign
        if parsegen.file_type() == 'elf' and parsegen.is_signed() and not sign and not parsegen.is_encrypted() and encrypt:
            raise RuntimeError('Cannot encrypt a signed unencrypted image without resigning '
                               'as the sign no longer matches the format change.')

        # Prevent updating signing attributes (without resigning) by current authority
        # if image is already signed by authority because old signature will not match
        if parsegen.is_signed(self.authority) and sign_attr and not i_sign:
            raise RuntimeError('Cannot update hash segment\'s signing attributes without resigning because signature will become invalid.')

        # Set the security mechanisms
        parsegen.integrity_check = security_policy_list[idx].integrity_check and (parsegen.contains_integrity_check() or integrity_check)
        parsegen.sign = security_policy_list[idx].sign and (parsegen.is_signed() or sign)
        parsegen.encrypt = security_policy_list[idx].encrypt and (False if decrypt else (parsegen.is_encrypted() or encrypt))

        # Get blob if populating encryption parameters:
        if encrypt:
            if encdec is None:
                raise RuntimeError('Encryptor is not set')
            parsegen.encryption_params = encdec.get_encryption_parameters_blob()
            # check if input image is a TA, if yes re-initialize encdec object with updated bitmap for manifest segment
            if int(image.signing_attributes.sw_id, 16) == 0xC:
                non_encrypt_segment_found, encrypted_segments_indices = self._get_encrypted_segments_index_list(parsegen._elf_parsegen.phdrs)
                if non_encrypt_segment_found and len(encrypted_segments_indices) > 0:
                    logger.info("Re-initializing encdec object for updated segment bitmap")
                    encdec = get_encdec(image, False, encrypted_segments_indices)
                    parsegen.encryption_params = encdec.get_encryption_parameters_blob()
                    parsegen.encdec = encdec

        elif parsegen.encryption_params and parsegen.encdec is not None:
            parsegen.encdec.update_encryption_parameters(parsegen.encryption_params)

        # Dump any debug data
        self.dump_parsegen_debug_data(image, parsegen)

        # If the security policy list contains more formats, call them
        if idx < len(security_policy_list) - 1:
            data = parsegen.get_wrapped_data()
            import tempfile
            tmp_fd = tempfile.NamedTemporaryFile(delete=False)
            tmp_fd.close()
            store_data_to_file(tmp_fd.name, data)

            # Backup the source path here
            src_image_dir_base = image.src_image.image_dir_base
            src_image_dir_ext = image.src_image.image_dir_ext
            src_image_name = image.src_image.image_name

            image.src_image.image_dir_base = os.path.dirname(tmp_fd.name)
            image.src_image.image_dir_ext = ''
            image.src_image.image_name = os.path.basename(tmp_fd.name)

            # Override debug dumped file prefix
            prefix_override = SecImageCore._get_prefix_override(prefix_override, file_type)

            try:
                data = self._process_secure_operation(image, progress, security_policy_list, sign_attr,
                                                      i_integrity_check, i_sign, i_encrypt, i_decrypt, idx + 1, prefix_override)
            finally:
                image.src_image.image_dir_base = src_image_dir_base
                image.src_image.image_dir_ext = src_image_dir_ext
                image.src_image.image_name = src_image_name

            os.remove(tmp_fd.name)

            parsegen.set_wrapped_data(data)

        # Sign the image
        if sign:
            self._status_updater(self._sign_image,
                                 image.status.sign,
                                 progress, True,
                                 image, parsegen)

        # Package and generate the output image file
        data = parsegen.get_data()
        if integrity_check:
            image.status.integrity_check.state = StatusInfo.SUCCESS
        if encrypt:
            image.status.encrypt.state = StatusInfo.SUCCESS

        if idx != 0:
            return data

        if decrypt:
            encryption_params_backup = parsegen.encryption_params
            parsegen.encryption_params = ''
            try:
                store_data_to_file(image.dest_image.decrypted_file, parsegen.get_data())
            finally:
                parsegen.encryption_params = encryption_params_backup

        else:
            store_data_to_file(image.dest_image.image_path, data)

        logger.info(('Signed ' if sign else '') +
                    ('& ' if sign and encrypt else '') +
                    ('Encrypted ' if encrypt else '') +
                    'image is stored at ' + image.dest_image.image_path)
        image.image_under_operation = image.dest_image.image_path

        # Do any post processing
        self._status_updater(self._post_process,
                             image.status.postprocess,
                             progress, True,
                             image, image.config.post_process.pil_splitter,
                             getattr(self._stager, '_meta_build_path', None))

        return parsegen

    def _process_validation(self, image, progress, security_policy_list,
                            i_val_image, i_val_integrity_check, i_val_sign, i_val_encrypt, idx=0, prefix_override=None):
        # TODO: Need to figure how to do this
        #image.dest_image._mid = 'validation'

        # Check bounds
        if len(security_policy_list) == 0:
            raise RuntimeError('Security policy list must not be empty.')
        elif len(security_policy_list) <= idx:
            raise RuntimeError('Security policy list length must be more than index.')

        # Get the current security policy
        file_type = security_policy_list[idx].file_type
        val_image = i_val_image
        val_integrity_check = security_policy_list[idx].integrity_check and i_val_integrity_check
        val_sign = security_policy_list[idx].sign and i_val_sign
        val_encrypt = security_policy_list[idx].encrypt and i_val_encrypt

        # Backup the source path here
        src_image_dir_base = image.src_image.image_dir_base
        src_image_dir_ext = image.src_image.image_dir_ext
        src_image_name = image.src_image.image_name

        # Update the souce image path
        image.src_image.image_dir_base = os.path.dirname(image.image_under_operation)
        image.src_image.image_dir_ext = ''
        image.src_image.image_name = os.path.basename(image.image_under_operation)

        try:
            # Create the encryptor object
            encdec = None
            if image.general_properties.selected_encryptor:
                c_path.create_debug_dir(image.dest_image.debug_dir_encdec)
                encdec = get_encdec(image, True)

            # Create the parsegen object
            file_type_backup = image.image_type.file_type
            encdec_backup = image.encdec
            image.image_type.file_type = file_type
            image.encdec = encdec
            try:
                parsegen = self._status_updater(self._create_parsegen_obj,
                                                image.status.validate_parsegen,
                                                progress,
                                                True,
                                                image,
                                                True,
                                                False,
                                                prefix_override)
            finally:
                image.image_type.file_type = file_type_backup
                image.encdec = encdec_backup

            # Validate the authority settings
            self.validate_authority_settings(self.authority,
                                             image.general_properties.secboot_version,
                                             image.general_properties.qti_sign,
                                             image.general_properties.oem_sign,
                                             image.general_properties.num_root_certs,
                                             parsegen.is_encrypted())

            # Prevent validation when using an encrypted key provider
            from sectools.features.isc.encryption_service.unified import encrypted_key_provider_id_supported
            encrypted_key_provider_id = image.signing_attributes.UIE_key
            if parsegen.is_encrypted() and encrypted_key_provider_id_supported(encrypted_key_provider_id):
                raise RuntimeError("The image is encrypted. Validation is not supported when using an encrypted key provider.\n"
                                   "Try again with validation disabled.")

            # Set the security mechanisms
            parsegen.integrity_check = parsegen.contains_integrity_check()
            parsegen.sign = parsegen.is_signed()
            parsegen.encrypt = parsegen.is_encrypted()

            # Validate parsegen
            if val_image:
                self._status_updater(self._validate_parsegen,
                                     image.status.validate_parsegen,
                                     progress, False,
                                     image, parsegen)

            # Validate integrity check
            if val_integrity_check:
                self._status_updater(self._validate_integrity_check,
                                     image.status.validate_integrity_check,
                                     progress, False,
                                     image, parsegen)

            # Validate sign
            if val_sign:
                self._status_updater(self._validate_sign,
                                     image.status.validate_sign,
                                     progress, False,
                                     image, parsegen)

            # Validate encrypt
            if val_encrypt:

                self._status_updater(self._validate_encrypt,
                                     image.status.validate_encrypt,
                                     progress, False,
                                     image, parsegen)

            # Dump any debug data
            self.dump_parsegen_debug_data(image, parsegen)

            # If the security policy list contains more formats, call them
            if idx < len(security_policy_list) - 1:
                data = parsegen.get_wrapped_data()
                import tempfile
                tmp_fd = tempfile.NamedTemporaryFile(prefix=security_policy_list[idx + 1].file_type, delete=False)
                tmp_fd.close()
                store_data_to_file(tmp_fd.name, data)

                # Backup the image_under_operation here
                image_under_operation_int = image.image_under_operation
                image.image_under_operation = tmp_fd.name

                # Override debug dumped file prefix
                prefix_override = SecImageCore._get_prefix_override(prefix_override, file_type)

                try:
                    self._process_validation(image, progress, security_policy_list,
                                             i_val_image, i_val_integrity_check, i_val_sign, i_val_encrypt, idx + 1, prefix_override)
                finally:
                    image.image_under_operation = image_under_operation_int

                os.remove(tmp_fd.name)

        finally:
            image.src_image.image_dir_base = src_image_dir_base
            image.src_image.image_dir_ext = src_image_dir_ext
            image.src_image.image_name = src_image_name

        return parsegen

    def _get_encrypted_segments_index_list(self, phdrs):
        encrypted_segments_indices = []
        found_not_encrypt_segments = False
        for indx, phdr in enumerate(phdrs):
            if phdr.p_type == PT_LOAD and phdr.f_os_segment_type not in NON_ENCRYPT_SEGMENT_OS_TYPE:
                encrypted_segments_indices.append(indx+2)
            elif phdr.f_os_segment_type in NON_ENCRYPT_SEGMENT_OS_TYPE:
                found_not_encrypt_segments = True
                logger.debug("LOAD segment " + str(indx+2) + " won't be encrypted")
        return (found_not_encrypt_segments, encrypted_segments_indices)

    def _create_parsegen(self, image, progress, security_policy_list, idx=0, prefix_override=None):
        from imageinfo import StatusInfo
        # Check bounds
        if len(security_policy_list) == 0:
            raise RuntimeError('Security policy list must not be empty.')
        elif len(security_policy_list) <= idx:
            raise RuntimeError('Security policy list length must be more than index.')
        file_type = security_policy_list[idx].file_type

        # Backup the source path here
        src_image_dir_base = image.src_image.image_dir_base
        src_image_dir_ext = image.src_image.image_dir_ext
        src_image_name = image.src_image.image_name

        # Update the souce image path
        image.src_image.image_dir_base = os.path.dirname(image.image_under_operation)
        image.src_image.image_dir_ext = ''
        image.src_image.image_name = os.path.basename(image.image_under_operation)

        try:
            # Create the encryptor object
            encdec = None
            if image.general_properties.selected_encryptor:
                c_path.create_debug_dir(image.dest_image.debug_dir_encdec)
                encdec = get_encdec(image, True)

            # Create the parsegen object
            file_type_backup = image.image_type.file_type
            encdec_backup = image.encdec
            image.image_type.file_type = file_type
            image.encdec = encdec
            try:
                parsegen = self._status_updater(self._create_parsegen_obj,
                                                image.status.parsegen,
                                                progress,
                                                True,
                                                image,
                                                validating=False,
                                                signing=False,
                                                prefix_override=prefix_override)
            finally:
                image.image_type.file_type = file_type_backup
                image.encdec = encdec_backup

            # Validate the authority settings
            self.validate_authority_settings(self.authority,
                                             image.general_properties.secboot_version,
                                             image.general_properties.qti_sign,
                                             image.general_properties.oem_sign,
                                             image.general_properties.num_root_certs,
                                             parsegen.is_encrypted())

            # Set the security mechanisms
            parsegen.integrity_check = parsegen.contains_integrity_check()
            parsegen.sign = parsegen.is_signed()
            parsegen.encrypt = parsegen.is_encrypted()

            # Dump any debug data
            self.dump_parsegen_debug_data(image, parsegen)

            # If the security policy list contains more formats, call them
            if idx < len(security_policy_list) - 1:
                data = parsegen.get_wrapped_data()
                import tempfile

                tmp_fd = tempfile.NamedTemporaryFile(prefix=security_policy_list[idx + 1].file_type, delete=False)
                tmp_fd.close()
                store_data_to_file(tmp_fd.name, data)

                # Backup the image_under_operation here
                image_under_operation_int = image.image_under_operation
                image.image_under_operation = tmp_fd.name

                # Override debug dumped file prefix
                prefix_override = SecImageCore._get_prefix_override(prefix_override, file_type)

                try:
                    self._create_parsegen(image, progress, security_policy_list, idx + 1, prefix_override)
                finally:
                    image.image_under_operation = image_under_operation_int

                os.remove(tmp_fd.name)

        finally:
            image.src_image.image_dir_base = src_image_dir_base
            image.src_image.image_dir_ext = src_image_dir_ext
            image.src_image.image_name = src_image_name

        return parsegen

    def _create_parsegen_obj(self, image, validating=False, signing=False, prefix_override=None, file_exists=True, parsegens=None, sign_attr=False):
        c_path.create_debug_dir(image.dest_image.debug_dir_parsegen)
        from sectools.features.isc.parsegen import get_parser
        parsegen = get_parser(image, validating, signing, prefix_override, file_exists, parsegens, sign_attr)

        # Check if parsegen authority settings are correct
        parsegen.authority = self.authority
        parsegen.validate_authority()

        return parsegen

    @staticmethod
    def validate_authority_settings(authority, secboot_version, qti_sign, oem_sign, num_root_certs, encrypt=False):
        if secboot_version != defines.SECBOOT_VERSION_1_0:
            if encrypt and authority != defines.highest_authority([oem_sign, qti_sign]):
                # Reserve encryption for the highest active authority #
                raise RuntimeError("Encryption is not allowed for: " + str(authority))
        if num_root_certs != 1 and authority == defines.AUTHORITY_QTI:
            raise RuntimeError("num_root_certs must be set to \"1\" for: " + str(authority))

    def _sign_image(self, image, parsegen):
        from sectools.features.isc.signer import get_signer

        # Check all other authorities and display if they have signed
        for authority in [x for x in defines.AUTHORITIES_SUPPORTED if x != self.authority]:
            if parsegen.is_signed(authority):
                logger.info(image.image_under_operation + ' is already ' + str(authority) + '-signed.')

        # Prevent resigning by authorities that previously signed that aren't the most recently signed authority
        previously_signed_authorities = []
        for authority in defines.AUTHORITIES_SUPPORTED:
            if parsegen.is_signed(authority):
                previously_signed_authorities.append(authority)
        last_signed_authority = defines.highest_authority([defines.AUTHORITY_OEM in previously_signed_authorities, defines.AUTHORITY_QTI in previously_signed_authorities])
        if self.authority != last_signed_authority and self.authority in previously_signed_authorities:
            raise RuntimeError("Cannot resign as {0} because image is already signed by {1}".format(self.authority, last_signed_authority))

        # Display sign status of signing authority
        logger.info(image.image_under_operation + ' is already ' + self.authority + '-signed. '
                    'Rerunning ' + self.authority + ' sign.' if parsegen.is_signed(self.authority)
                    else 'Performing ' + self.authority + ' sign on image: ' + image.image_under_operation)

        signer = get_signer(image.config)

        sign_assets = signer.sign(parsegen.data_to_sign, image, image.dest_image.debug_dir_signer, parsegen.is_data_hash, parsegen.get_hash_segment_metadata())

        parsegen.data_signature = sign_assets.signature
        parsegen.cert_chain = sign_assets.cert_chain

        # Dump any debug information
        self.dump_signer_debug_data(image, sign_assets, parsegen)

    @staticmethod
    def pil_split(src, prefix):
        from sectools.common.parsegen.elf.format import ParseGenElf, pack_phdrs, PF_OS_SEGMENT_HASH

        # Load the data
        p_obj = ParseGenElf(load_data_from_file(src))

        # File names
        elfhdr = prefix + '.mdt'

        # Cleanup
        for eachpattern in [elfhdr, (prefix + '.b*')]:
            import glob
            for eachfile in glob.glob(eachpattern):
                try: os.remove(eachfile)
                except Exception: pass

        # Create the mdt data
        elfdata = p_obj.ehdr.pack() + pack_phdrs(p_obj.phdrs)

        # Dump the segments
        for idx, phdr in enumerate(p_obj.phdrs):
            path = prefix + ('.b%02d' % idx)
            store_data_to_file(path, p_obj.segments[phdr])
            if phdr.f_os_segment_type == PF_OS_SEGMENT_HASH:
                elfdata += p_obj.segments[phdr]

        # Dump the final elfhdr mdt
        store_data_to_file(elfhdr, elfdata)

    def _post_process(self, image, pil_splitter_path, meta_build_path):
        ''' Replacement tags in postsign commands for images. '''
        TAG_OUTPUT_DIR = '$(OUTPUT_DIR)'
        TAG_PIL_SPLITTER = '$(PIL_SPLITTER)'
        TAG_IMAGE_FILE = '$(IMAGE_FILE)'
        REPL_META_PATH = '$(META_BUILD)'

        if image.pil_split:
            image_file = image.image_under_operation
            SecImageCore.pil_split(image_file, os.path.splitext(image_file)[0])

        if image.post_process_commands:
            # Ensure pil splitter is available
            if pil_splitter_path.find(REPL_META_PATH) != -1:
                if not meta_build_path:
                    raise RuntimeError('Metabuild path is not available for pil splitter')
                pil_splitter_path = pil_splitter_path.replace(REPL_META_PATH, meta_build_path)

            if not c_path.validate_file(pil_splitter_path):
                raise RuntimeError('Cannot access pil splitter at: ' + pil_splitter_path)

            # Run all the commands
            for cmd in [c.strip() for c in image.post_process_commands.split()]:
                # Perform any needed replacements
                cmd = cmd.replace(TAG_OUTPUT_DIR, os.path.dirname(image.image_under_operation))
                cmd = cmd.replace(TAG_PIL_SPLITTER, pil_splitter_path)
                cmd = cmd.replace(TAG_IMAGE_FILE, image.image_under_operation)

                logger.info('Running postsign command: ' + cmd)
                err = os.system(cmd)
                logger.info('Result: ' + str(err))

    def _validate_parsegen(self, image, parsegen):
        pass

    def _validate_integrity_check(self, image, parsegen):
        parsegen.validate_hash_segment_metadata(self.authority)

    def _validate_sign(self, image, parsegen):
        from sectools.features.isc.signer import get_signer
        if parsegen.is_signed():
            signer = get_signer(image.config)
            if signer.validate(parsegen, image.validation_root_cert_hash, image):
                logger.info('Image ' + image.image_under_operation + ' signature is valid')
            else:
                raise RuntimeError('Image ' + image.image_under_operation + ' signature is not valid')
        else:
            raise CustomError('Image ' + image.image_under_operation + ' is not signed')

    def _validate_encrypt(self, image, parsegen):
        if parsegen.is_encrypted():
            logger.info('Image ' + image.image_under_operation + ' is encrypted')
        else:
            raise CustomError('Image ' + image.image_under_operation + ' is not encrypted')

    def _status_updater(self, method, status, progress, raise_err, *args, **kwargs):
        from imageinfo import ImageInfo, StatusInfo
        try:
            retval = method(*args, **kwargs)
            status.state = StatusInfo.SUCCESS
            progress.push()
            return retval
        except Exception as e:
            status.state = StatusInfo.ERROR
            status.error = str(e)
            progress.push()
            if raise_err:
                raise
            else:
                if isinstance(e, CustomError):
                    logger.info(status.error)
                else:
                    logger.error(status.error)

    def dump_parsegen_debug_data(self, image, parsegen):
        if image.dest_image.debug_dir_parsegen is None:
            return

        so = parsegen
        fp = image.dest_image
        from imageinfo import DestImagePath
        assert isinstance(fp, DestImagePath)

        debug_logs = []
        try: debug_logs.append((so.get_data(False, False, False), fp.debug_file_parsegen_unsigned))
        except Exception: pass
        try: debug_logs.append((so.data_to_sign, fp.debug_file_parsegen_tosign))
        except Exception: pass
        try: debug_logs.append((so.cert_chain, fp.debug_file_parsegen_cert_chain))
        except Exception: pass
        try: debug_logs.append((so.data_signature, fp.debug_file_parsegen_signature))
        except Exception: pass
        try: debug_logs.append((so.get_data(True, False, False), fp.debug_file_parsegen_integrity_check))
        except Exception: pass
        try: debug_logs.append((so.get_data(True, True, False), fp.debug_file_parsegen_signed))
        except Exception: pass
        try: debug_logs.append((so.get_data(True, True, True), fp.debug_file_parsegen_encrypted))
        except Exception: pass

        for data, debug_file in debug_logs:
            try: store_data_to_file(debug_file, data)
            except Exception: logger.debug2('Failed to save debug file ' + debug_file + '\n'
                                            '    ' + str(sys.exc_info()[1]))

    def dump_signer_debug_data(self, image, sign_assets, parsegen):
        if image.dest_image.debug_dir_signer is None:
            return
        c_path.create_debug_dir(image.dest_image.debug_dir_signer)

        sa = sign_assets
        fp = image.dest_image
        from imageinfo import DestImagePath
        assert isinstance(fp, DestImagePath)

        # Backup parsegen authority
        authority = parsegen.authority

        # QTI Signature and Cert Chain
        parsegen.authority = defines.AUTHORITY_QTI
        data_signature_qti = parsegen.data_signature
        cert_chain_qti = parsegen.cert_chain

        # OEM Signature and Cert Chain
        parsegen.authority = defines.AUTHORITY_OEM
        data_signature = parsegen.data_signature
        cert_chain = parsegen.cert_chain

        # Restore authority
        parsegen.authority = authority

        debug_logs = [(sa.root_cert, fp.debug_file_signer_root_cert),
                      (sa.attestation_ca_cert, fp.debug_file_signer_attestation_ca_cert),
                      (sa.attestation_cert, fp.debug_file_signer_attestation_cert),
                      (data_signature, fp.debug_file_signer_signature),
                      (cert_chain, fp.debug_file_signer_cert_chain),
                      (data_signature_qti, fp.debug_file_signer_qti_signature),
                      (cert_chain_qti, fp.debug_file_signer_qti_cert_chain)]

        # Save the private attributes too
        debug_logs += [(sa.root_key, fp.debug_file_signer_root_key),
                       (sa.attestation_ca_key, fp.debug_file_signer_attestation_ca_key),
                       (sa.attestation_key, fp.debug_file_signer_attestation_key)]

        for data, debug_file in debug_logs:
            try: store_data_to_file(debug_file, data)
            except Exception: logger.debug2('Failed to save debug file ' + debug_file + '\n'
                                            '    ' + str(sys.exc_info()[1]))

class CustomError(RuntimeError):
    """
    CustomError class to exercise different processing than RuntimeError.
    """
    pass

#------------------------------------------------------------------------------
# Restrict all import
#------------------------------------------------------------------------------
__all__ = ['SecImageCore',
           'cfgparser',
           'cryptoutils',
           'parsegen',
           'CustomError']

