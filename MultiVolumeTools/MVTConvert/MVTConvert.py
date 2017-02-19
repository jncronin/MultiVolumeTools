import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# MVTConvert
#

class MVTConvert(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MVTConvert" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Splits the individual frames of a single-slice 
    MultiVolume to a multi-slice Volume to allow easier 
    editing.  Optionally adds padding at the start and end, 
    and allows sub-sampling of only certain frames within 
    the MultiVolume.  For example, Start frame = 2, 
    Number of frames = 3, Frame Interval = 4, ZSlices = 5, 
    Pad = True would generate an output of: BLANK, 2, 2, 2, 
    2, 2, 6, 6, 6, 6, 6, 10, 10, 10, 10, 10, BLANK. 
    Optionally creates a ready-to-go LabelMap for the 
    output volume.    
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# MVTConvertWidget
#

class MVTConvertWidget(ScriptedLoadableModuleWidget):
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
    self.inputSelector.nodeTypes = ["vtkMRMLMultiVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)
	
    # output volume template
    #
    self.ovol = slicer.qMRMLNodeComboBox()
    self.ovol.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.ovol.selectNodeUponCreation = True
    self.ovol.addEnabled = True
    self.ovol.removeEnabled = False
    self.ovol.noneEnabled = False
    self.ovol.renameEnabled = True
    self.ovol.showHidden = False
    self.ovol.showChildNodeTypes = False
    self.ovol.setMRMLScene( slicer.mrmlScene )
    self.ovol.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.ovol)
    
    self.sframe = qt.QLineEdit()
    self.sframe.text = '0'
    parametersFormLayout.addRow("Start frame: ", self.sframe)
    
    self.nframes = qt.QLineEdit()
    self.nframes.text = '40'
    parametersFormLayout.addRow("Number of frames: ", self.nframes)
    
    self.finterval = qt.QLineEdit()
    self.finterval.text = '5'
    parametersFormLayout.addRow("Frame interval: ", self.finterval)
    
    self.zslices = qt.QLineEdit()
    self.zslices.text = '1'
    parametersFormLayout.addRow("ZSlices per frame: ", self.zslices)
    
    self.pad = qt.QCheckBox()
    self.pad.setChecked(True)
    parametersFormLayout.addRow("Pad with blank frame: ", self.pad)
    
    self.createLabel = qt.QCheckBox()
    self.createLabel.setChecked(False)
    parametersFormLayout.addRow("Create Label Map: ", self.createLabel)
    
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Split frames for editing")
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
    self.ovol.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect);

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.ovol.currentNode() is not None)

  def onApplyButton(self):
    logic = MVTConvertLogic()
    logic.run(self.inputSelector.currentNode(), self.ovol.currentNode(), int(self.sframe.text), int(self.nframes.text), int(self.finterval.text), int(self.zslices.text), self.pad.isChecked(), self.createLabel.isChecked(), self.progbar)

#
# pig_dynLogic
#

class MVTConvertLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() == None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData) 

  def run(self, input_vol, output_vol, sframe, nframes, finterval, zslices, to_pad = True, create_label = False, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')

    a = slicer.util.array(input_vol.GetName())
    max_y = len(a[0])
    max_x = len(a[0][0])

    vl = slicer.modules.volumes.logic()
	
    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
      
    # Get some information about the input volume for eventually exporting
    instUids = input_vol.GetAttribute('DICOM.instanceUIDs').split()
    filename = slicer.dicomDatabase.fileForInstance(instUids[0])
    output_vol.SetAttribute('pig_dyn.AcquisitionDateTime', slicer.dicomDatabase.fileValue(filename, '0008,002a'))
    output_vol.SetAttribute('pig_dyn.SourceName', input_vol.GetName())
    output_vol.SetAttribute('pig_dyn.SeriesName', slicer.dicomDatabase.fileValue(filename, '0020,0011'))
    output_vol.SetAttribute('pig_dyn.PatientName', slicer.dicomDatabase.fileValue(filename, '0010,0010'))
    
    # Add 2 extra frames (one at start and one at end) to enable segregation using
    # LevelTracingEffect
    
    total_frames = nframes
    if(to_pad):
      total_frames = total_frames + 2
    
    imageSize=[max_x, max_y, zslices * total_frames]
    imageSpacing=input_vol.GetSpacing()
    voxelType=vtk.VTK_SHORT
    # Create an empty image volume
    imageData=vtk.vtkImageData()
    imageData.SetDimensions(imageSize)
    imageData.AllocateScalars(voxelType, 1)
    thresholder=vtk.vtkImageThreshold()
    thresholder.SetInputData(imageData)
    thresholder.SetInValue(0)
    thresholder.SetOutValue(0)
    # Create volume node
    volumeNode = output_vol
    #volumeNode=slicer.vtkMRMLScalarVolumeNode()
    #vname = output_vol;
    #volumeNode.SetName(vname)
    volumeNode.SetSpacing(imageSpacing)
    volumeNode.SetOrigin(input_vol.GetOrigin())
    vm = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASDirectionMatrix(vm)
    volumeNode.SetIJKToRASDirectionMatrix(vm)
    volumeNode.SetImageDataConnection(thresholder.GetOutputPort())
    # Add volume to scene
    #slicer.mrmlScene.AddNode(volumeNode)
    displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    colorNode = slicer.util.getNode('Grey')
    displayNode.SetAndObserveColorNodeID(colorNode.GetID())
    volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    volumeNode.CreateDefaultStorageNode()
    displayNode.AutoWindowLevelOff()
    displayNode.SetWindow(200)
    displayNode.SetLevel(0)
    displayNode.SetInterpolate(0)
    da = slicer.util.array(volumeNode.GetID())
    
    offset_frame = 0
    if(to_pad):
      offset_frame = 1
    
    for fid in xrange(0, nframes):
      for z in xrange(0, zslices):
        for y in xrange(0, max_y):
          for x in xrange(0, max_x):
            da[z + fid * zslices + offset_frame][y][x] = a[0][y][x][sframe + fid * finterval]
      
      logging.info('Processed frame %d' % fid)
	  
      if pb is None:
        pass
      else:
        pb.setValue((fid + 1) * 100 / nframes)
        slicer.app.processEvents()
        
    if(create_label):
      vl.CreateLabelVolume(slicer.mrmlScene, volumeNode, volumeNode.GetName() + '-label')

    logging.info('Processing completed')

    return True


class MVTConvertTest(ScriptedLoadableModuleTest):
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
    self.test_MVTConvert1()

  def test_MVTConvert1(self):
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
