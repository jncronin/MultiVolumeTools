cmake_minimum_required(VERSION 2.8.9)

project(MultiVolumeTools)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://github.com/jncronin/MultiVolumeTools")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "John Cronin (KCL)")
set(EXTENSION_DESCRIPTION "Tools for converting a single slice MultiVolume into a multi-slice Volume, and then exporting that Volume to a proprietary binary format whilst preserving certain DICOM tags.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/pig_dyn.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/pig_dyn/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(MVTBinaryExport)
add_subdirectory(MVTConvert)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
