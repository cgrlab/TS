/* Copyright (C) 2010 Ion Torrent Systems, Inc. All Rights Reserved */

#ifndef CUDA_ERROR_H
#define CUDA_ERROR_H




#ifndef NO_CUDA_DEBUG
#define CUDA_ERROR_CHECK()                                                                     \
{                                                                                              \
    cudaError_t err = cudaGetLastError();                                                      \
    if ( err != cudaSuccess && err != cudaErrorSetOnActiveProcess ) {                          \
        std::cout << " +----------------------------------------" << std::endl                 \
                  << " | ** CUDA ERROR! ** " << std::endl                                      \
                  << " | Error: " << err << std::endl                                          \
                  << " | Msg: " << cudaGetErrorString(err) << std::endl                        \
                  << " | File: " << __FILE__ << std::endl                                      \
                  << " | Line: " << __LINE__ << std::endl                                      \
                  << " +----------------------------------------" << std::endl << std::flush;  \
                  exit(-1);                                                                    \
      }                                                                                        \
}     
#else
#define CUDA_ERROR_CHECK() {}
#endif


/* cuda Error Codes:
  cudaSuccess                           =      0,   ///< No errors
  cudaErrorMissingConfiguration         =      1,   ///< Missing configuration error
  cudaErrorMemoryAllocation             =      2,   ///< Memory allocation error
  cudaErrorInitializationError          =      3,   ///< Initialization error
  cudaErrorLaunchFailure                =      4,   ///< Launch failure
  cudaErrorPriorLaunchFailure           =      5,   ///< Prior launch failure
  cudaErrorLaunchTimeout                =      6,   ///< Launch timeout error
  cudaErrorLaunchOutOfResources         =      7,   ///< Launch out of resources error
  cudaErrorInvalidDeviceFunction        =      8,   ///< Invalid device function
  cudaErrorInvalidConfiguration         =      9,   ///< Invalid configuration
  cudaErrorInvalidDevice                =     10,   ///< Invalid device
  cudaErrorInvalidValue                 =     11,   ///< Invalid value
  cudaErrorInvalidPitchValue            =     12,   ///< Invalid pitch value
  cudaErrorInvalidSymbol                =     13,   ///< Invalid symbol
  cudaErrorMapBufferObjectFailed        =     14,   ///< Map buffer object failed
  cudaErrorUnmapBufferObjectFailed      =     15,   ///< Unmap buffer object failed
  cudaErrorInvalidHostPointer           =     16,   ///< Invalid host pointer
  cudaErrorInvalidDevicePointer         =     17,   ///< Invalid device pointer
  cudaErrorInvalidTexture               =     18,   ///< Invalid texture
  cudaErrorInvalidTextureBinding        =     19,   ///< Invalid texture binding
  cudaErrorInvalidChannelDescriptor     =     20,   ///< Invalid channel descriptor
  cudaErrorInvalidMemcpyDirection       =     21,   ///< Invalid memcpy direction
  cudaErrorAddressOfConstant            =     22,   ///< Address of constant error
  cudaErrorTextureFetchFailed           =     23,   ///< Texture fetch failed
  cudaErrorTextureNotBound              =     24,   ///< Texture not bound error
  cudaErrorSynchronizationError         =     25,   ///< Synchronization error
  cudaErrorInvalidFilterSetting         =     26,   ///< Invalid filter setting
  cudaErrorInvalidNormSetting           =     27,   ///< Invalid norm setting
  cudaErrorMixedDeviceExecution         =     28,   ///< Mixed device execution
  cudaErrorCudartUnloading              =     29,   ///< CUDA runtime unloading
  cudaErrorUnknown                      =     30,   ///< Unknown error condition
  cudaErrorNotYetImplemented            =     31,   ///< Function not yet implemented
  cudaErrorMemoryValueTooLarge          =     32,   ///< Memory value too large
  cudaErrorInvalidResourceHandle        =     33,   ///< Invalid resource handle
  cudaErrorNotReady                     =     34,   ///< Not ready error
  cudaErrorInsufficientDriver           =     35,   ///< CUDA runtime is newer than driver
  cudaErrorSetOnActiveProcess           =     36,   ///< Set on active process error
  cudaErrorNoDevice                     =     38,   ///< No available CUDA device
  cudaErrorStartupFailure               =   0x7f,   ///< Startup failure
*/

#endif // CUDA_ERROR_H
