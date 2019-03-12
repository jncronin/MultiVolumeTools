import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# CPPDiff
#

class CPPDiff(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Control Point Differentiator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Differentiate a vector volume containing control points to give individual R,A,S scalar volumes of velocity.
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# CPPDiffWidget
#

class CPPDiffWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLVectorVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Control Point volume." )
    parametersFormLayout.addRow("Control Points Volume: ", self.inputSelector)

    # output volumes
    self.r = slicer.qMRMLNodeComboBox()
    self.r.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.r.selectNodeUponCreation = True
    self.r.addEnabled = True
    self.r.removeEnabled = False
    self.r.noneEnabled = False
    self.r.renameEnabled = True
    self.r.showHidden = False
    self.r.showChildNodeTypes = False
    self.r.setMRMLScene( slicer.mrmlScene )
    self.r.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output R Volume: ", self.r)
    self.a = slicer.qMRMLNodeComboBox()
    self.a.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.a.selectNodeUponCreation = True
    self.a.addEnabled = True
    self.a.removeEnabled = False
    self.a.noneEnabled = False
    self.a.renameEnabled = True
    self.a.showHidden = False
    self.a.showChildNodeTypes = False
    self.a.setMRMLScene( slicer.mrmlScene )
    self.a.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output A Volume: ", self.a)
    self.s = slicer.qMRMLNodeComboBox()
    self.s.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.s.selectNodeUponCreation = True
    self.s.addEnabled = True
    self.s.removeEnabled = False
    self.s.noneEnabled = False
    self.s.renameEnabled = True
    self.s.showHidden = False
    self.s.showChildNodeTypes = False
    self.s.setMRMLScene( slicer.mrmlScene )
    self.s.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output S Volume: ", self.s)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Run")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)
    	
    #
    # Progress Bar
    #
    self.progbar = qt.QProgressBar()
    self.progbar.setValue(0)
    parametersFormLayout.addRow(self.progbar)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.r.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.a.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.s.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.r.currentNode() is not None) & (self.a.currentNode() is not None) & (self.s.currentNode() is not None)

  def onApplyButton(self):
    logic = CPPDiffLogic()
    logic.run(self.inputSelector.currentNode(), self.r.currentNode(), self.a.currentNode(), self.s.currentNode(), self.progbar)

#
# pig_dynLogic
#

class CPPDiffLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, input_vol, r, a, s, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_im = input_vol.GetImageData()
    input_shape = list(input_im.GetDimensions())
    input_shape.reverse()

    max_z = input_shape[0]
    max_y = input_shape[1]
    max_x = input_shape[2]
    idata = vtk.util.numpy_support.vtk_to_numpy(input_im.GetPointData().GetScalars()).reshape([max_z, max_y, max_x, 3])
   
    # determine new image size
    imageSpacing=input_vol.GetSpacing()


    # get transform matrix
    mtform = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASMatrix(mtform)

    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
         
    imageSize=[max_x, max_y, max_z]

    imageDataR=vtk.vtkImageData()
    imageDataR.SetDimensions(max_x, max_y, max_z)
    imageDataR.AllocateScalars(vtk.VTK_FLOAT, 1)
    imageDataA=vtk.vtkImageData()
    imageDataA.SetDimensions(max_x, max_y, max_z)
    imageDataA.AllocateScalars(vtk.VTK_FLOAT, 1)
    imageDataS=vtk.vtkImageData()
    imageDataS.SetDimensions(max_x, max_y, max_z)
    imageDataS.AllocateScalars(vtk.VTK_FLOAT, 1)

    output_scalarsR = imageDataR.GetPointData().GetScalars()
    output_scalarsA = imageDataA.GetPointData().GetScalars()
    output_scalarsS = imageDataS.GetPointData().GetScalars()
    dr = vtk.util.numpy_support.vtk_to_numpy(output_scalarsR).reshape([max_z, max_y, max_x])
    da = vtk.util.numpy_support.vtk_to_numpy(output_scalarsA).reshape([max_z, max_y, max_x])
    ds = vtk.util.numpy_support.vtk_to_numpy(output_scalarsS).reshape([max_z, max_y, max_x])

    # put in the actual data
    for z in xrange(0, max_z):
      for y in xrange(0, max_y):
        for x in xrange(0, max_x):
          ijkcoord = (x, y, z, 1.0)
          rascoord = mtform.MultiplyPoint(ijkcoord)

          dr[z,y,x] = idata[z,y,x,0] - rascoord[0]
          da[z,y,x] = idata[z,y,x,1] - rascoord[1]
          ds[z,y,x] = idata[z,y,x,2] - rascoord[2]
      
      if pb is None:
        pass
      else:
        pb.setValue(100 * z / max_z)
        slicer.app.processEvents()

    # normalize to mean movement (i.e. similar to centre of lung)
    #dr[:,:,:] = dr[:,:,:] - np.mean(dr)
    #da[:,:,:] = da[:,:,:] - np.mean(da)
    #ds[:,:,:] = ds[:,:,:] - np.mean(ds)
       
    imageDataR.Modified()
    output_scalarsR.Modified()
    imageDataA.Modified()
    output_scalarsA.Modified()
    imageDataS.Modified()
    output_scalarsS.Modified()
    
    thresholderR=vtk.vtkImageThreshold()
    thresholderR.SetInputData(imageDataR)
    thresholderR.Update()
    thresholderA=vtk.vtkImageThreshold()
    thresholderA.SetInputData(imageDataA)
    thresholderA.Update()
    thresholderS=vtk.vtkImageThreshold()
    thresholderS.SetInputData(imageDataS)
    thresholderS.Update()

    # Create volume nodes
    r.SetSpacing(imageSpacing)
    r.SetOrigin(input_vol.GetOrigin())
    a.SetSpacing(imageSpacing)
    a.SetOrigin(input_vol.GetOrigin())
    s.SetSpacing(imageSpacing)
    s.SetOrigin(input_vol.GetOrigin())

    vm = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASDirectionMatrix(vm)
    r.SetIJKToRASDirectionMatrix(vm)
    a.SetIJKToRASDirectionMatrix(vm)
    s.SetIJKToRASDirectionMatrix(vm)

    r.SetImageDataConnection(thresholderR.GetOutputPort())
    a.SetImageDataConnection(thresholderA.GetOutputPort())
    s.SetImageDataConnection(thresholderS.GetOutputPort())

    # Colour lookup table
    colorNode = slicer.util.getNode('FullRainbow')

    # Add volume to scene
    displayNodeR=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNodeR)
    displayNodeR.SetAndObserveColorNodeID(colorNode.GetID())
    r.SetAndObserveDisplayNodeID(displayNodeR.GetID())
    r.CreateDefaultStorageNode()

    displayNodeA=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNodeA)
    displayNodeA.SetAndObserveColorNodeID(colorNode.GetID())
    a.SetAndObserveDisplayNodeID(displayNodeA.GetID())
    a.CreateDefaultStorageNode()

    displayNodeS=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNodeS)
    displayNodeS.SetAndObserveColorNodeID(colorNode.GetID())
    s.SetAndObserveDisplayNodeID(displayNodeS.GetID())
    s.CreateDefaultStorageNode()

    # generate custom window/levels.  We want to encompass +/- 10% of max range
    #  in R/A/S direction i.e. window is 20% and level is 0
    displayNodeR.SetAutoWindowLevel(0)
    displayNodeR.SetWindowLevel(abs(0.2 * max_x * imageSpacing[0]), 0)
    displayNodeA.SetAutoWindowLevel(0)
    displayNodeA.SetWindowLevel(abs(0.2 * max_y * imageSpacing[1]), 0)
    displayNodeS.SetAutoWindowLevel(0)
    displayNodeS.SetWindowLevel(abs(0.2 * max_z * imageSpacing[2]), 0)


    logging.info('Processing completed')
    if pb is None:
      pass
    else:
      pb.setValue(100)
      slicer.app.processEvents()

    # Assign to slice viewers
    slicer.util.setSliceViewerLayers(background=s, foreground=None)
    for sliceViewName in slicer.app.layoutManager().sliceViewNames():
     sw = slicer.app.layoutManager().sliceWidget(sliceViewName)
     sw.sliceLogic().FitSliceToAll()

    return True


class CPPDiffTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_CPPDiff1()

  def test_CPPDiff1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = pig_dynLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
