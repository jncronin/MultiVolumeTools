import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# AtelectSegment
#

class AtelectSegment(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "AtelectSegment" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Automatically segment an image based on density as per Gattinoni thresholds.  Optionally mask the output with a label map.
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# AtelectSegmentWidget
#

class AtelectSegmentWidget(ScriptedLoadableModuleWidget):
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
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)
	
    # input mask map
    #
    self.imask = slicer.qMRMLNodeComboBox()
    self.imask.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.imask.selectNodeUponCreation = False
    self.imask.addEnabled = False
    self.imask.removeEnabled = False
    self.imask.noneEnabled = True
    self.imask.renameEnabled = False
    self.imask.showHidden = False
    self.imask.showChildNodeTypes = False
    self.imask.setMRMLScene( slicer.mrmlScene )
    self.imask.setToolTip( "Pick the mask volume.." )
    parametersFormLayout.addRow("Mask Label Map: ", self.imask)

    # output label map
    self.ovol = slicer.qMRMLNodeComboBox()
    self.ovol.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.ovol.selectNodeUponCreation = True
    self.ovol.addEnabled = True
    self.ovol.removeEnabled = False
    self.ovol.noneEnabled = False
    self.ovol.renameEnabled = True
    self.ovol.showHidden = False
    self.ovol.showChildNodeTypes = False
    self.ovol.setMRMLScene( slicer.mrmlScene )
    self.ovol.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Label Map: ", self.ovol)

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
    self.progbar = qt.QProgressBar();
    self.progbar.setValue(0);
    parametersFormLayout.addRow(self.progbar);

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ovol.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.ovol.currentNode() is not None)

  def onApplyButton(self):
    logic = AtelectSegmentLogic()
    logic.run(self.inputSelector.currentNode(), self.imask.currentNode(), self.ovol.currentNode(), self.progbar)

#
# pig_dynLogic
#

class AtelectSegmentLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, input_vol, input_mask, output_vol, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_im = input_vol.GetImageData()
    input_shape = list(input_im.GetDimensions())
    input_shape.reverse()
    a = vtk.util.numpy_support.vtk_to_numpy(input_im.GetPointData().GetScalars()).reshape(input_shape)
    
    #a = slicer.util.array(input_vol.GetName())
    max_z = input_shape[0]
    max_y = input_shape[1]
    max_x = input_shape[2]

    vl = slicer.modules.volumes.logic()
	
    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
         
    imageSize=[max_x, max_y, max_z]
    imageSpacing=input_vol.GetSpacing()
    voxelType=input_vol.GetImageData().GetScalarType()
    # Create an empty image volume
    imageData=vtk.vtkImageData()
    #imageData.DeepCopy(input_vol.GetImageData())
    imageData.SetDimensions(max_x, max_y, max_z)
    imageData.AllocateScalars(vtk.VTK_SHORT, 1)

    output_scalars = imageData.GetPointData().GetScalars()
    da = vtk.util.numpy_support.vtk_to_numpy(output_scalars).reshape(input_shape)
    #da = slicer.util.array(volumeNode.GetID())

    o = np.zeros_like(a)

    # if floating point, assume bounded 0 to 1.0
    if input_im.GetScalarType() == vtk.VTK_FLOAT:
      o[np.where((a >= 0) & (a < 0.1))] = 1
      o[np.where((a >= 0.1) & (a < 0.5))] = 2
      o[np.where((a >= 0.5) & (a < 0.9))] = 3
      o[np.where((a >= 0.9) & (a <= 1.0))] = 4
    else:
      o[np.where((a > -100) & (a <= 100))] = 1
      o[np.where((a > -500) & (a <= -100))] = 2
      o[np.where((a > -900) & (a <= -500))] = 3
      o[np.where((a > -1000) & (a <= -900))] = 4

    # mask if requested
    if input_mask is not None:
      im_im = input_mask.GetImageData()
      b = vtk.util.numpy_support.vtk_to_numpy(im_im.GetPointData().GetScalars()).reshape(input_shape)
      o[np.where(b == 0)] = 0

    da[:,:,:] = o
        
    imageData.Modified()
    output_scalars.Modified()
    
    thresholder=vtk.vtkImageThreshold()
    thresholder.SetInputData(imageData)
    #thresholder.SetInValue(0)
    #thresholder.SetOutValue(0)
    # Create volume node
    volumeNode = output_vol
    volumeNode.SetSpacing(imageSpacing)
    volumeNode.SetOrigin(input_vol.GetOrigin())
    vm = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASDirectionMatrix(vm)
    volumeNode.SetIJKToRASDirectionMatrix(vm)
    volumeNode.SetImageDataConnection(thresholder.GetOutputPort())
    # Add volume to scene
    displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    colorNode = slicer.util.getNode('GenericAnatomyColors')
    displayNode.SetAndObserveColorNodeID(colorNode.GetID())
    volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    volumeNode.CreateDefaultStorageNode()
    displayNode.AutoWindowLevelOff()
    displayNode.SetWindow(float(5))
    displayNode.SetLevel(float(4 + 1) / 2.0)
    #displayNode.SetInterpolate(0)
    
    logging.info('Processing completed %d %d' % (imageData.GetScalarRange()[0], imageData.GetScalarRange()[1]))

    # Assign to red slice viewe
    lm = slicer.app.layoutManager()
    sl = lm.sliceWidget("Red").sliceLogic()
    red_cn = sl.GetSliceCompositeNode()
    red_cn.SetLabelVolumeID(volumeNode.GetID())
    red_cn.SetBackgroundVolumeID(input_vol.GetID())

    return True


class AtelectSegmentTest(ScriptedLoadableModuleTest):
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
    self.test_AtelectSegment1()

  def test_AtelectSegment1(self):
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
