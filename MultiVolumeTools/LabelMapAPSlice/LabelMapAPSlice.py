import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# LabelMapAPSlice
#

class LabelMapAPSlice(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LabelMapAPSlice" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Divides a label map into anterior-posterior slices  
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# LabelMapAPSliceWidget
#

class LabelMapAPSliceWidget(ScriptedLoadableModuleWidget):
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
    self.inputSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Label Map: ", self.inputSelector)
	
    # output volume template
    #
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
    
    self.slices = qt.QLineEdit()
    self.slices.text = '0'
    parametersFormLayout.addRow("Slices: ", self.slices)
       
    self.equal_sizes = qt.QCheckBox()
    self.equal_sizes.setChecked(False)
    parametersFormLayout.addRow("Make slices equal areas: ", self.equal_sizes)
       
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
    self.slices.textEdited.connect(self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.ovol.currentNode() is not None) & (int(self.slices.text) > 0)

  def onApplyButton(self):
    logic = LabelMapAPSliceLogic()
    logic.run(self.inputSelector.currentNode(), self.ovol.currentNode(), int(self.slices.text), self.equal_sizes.isChecked(), self.progbar)

#
# pig_dynLogic
#

class LabelMapAPSliceLogic(ScriptedLoadableModuleLogic):
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

  def run(self, input_vol, output_vol, slices, equal_sizes, pb = None):
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
       
    for z in xrange(0, max_z):
      # first decide on the first and last set lines
      first_set = max_y
      last_set = 0
      set_count = 0

      aset = np.where(a[z] > 0)[0]
      set_count = len(aset)
      if(set_count > 0):
        first_set = min(aset)
        last_set = max(aset)
            
      logging.info('First set %d last set %d' % (first_set, last_set))
      
      if(set_count > 0):
        # decide on the threshold lines
        zone_starts = []
        zone_ends = []
        
        if(equal_sizes):
          prev_zone = 0
          cur_pt = -1
          cur_start = first_set
          for y in xrange(first_set, last_set + 1):
            for x in xrange(0, max_x):
              cp = a[z][y][x]
              if cp != 0:
                cur_pt = cur_pt + 1
                cur_zone = cur_pt * slices / set_count
                if cur_zone != prev_zone:
                  zs = cur_start
                  ze = y
                  zone_starts.append(zs)
                  zone_ends.append(ze)
                  cur_start = y
                  prev_zone = cur_zone
          zone_starts.append(cur_start)
          zone_ends.append(last_set + 1)
        else:
          for zone in xrange(0, slices):
            zs = (last_set - first_set) * zone / slices + first_set
            ze = (last_set - first_set) * (zone + 1) / slices + first_set
            zone_starts.append(zs)
            zone_ends.append(ze)
            logging.info('Zone %d to %d' % (zs, ze))
          
        # copy data
        logging.info('Processing frame')
        input_z = a[z]
        input_mask = np.zeros_like(input_z)

        for zone in xrange(0, slices):
          input_mask[xrange(zone_starts[zone], zone_ends[zone])] = zone + 1
        
        input_mask[np.where(input_z == 0)] = 0
        da[z] = input_mask
      
      #imageData.Modified()
      #imageData.GetPointData().GetScalars().Modified()
      #volumeNode.Modified()
      logging.info('Processed frame %d' % z)
	  
      if pb is None:
        pass
      else:
        pb.setValue((z + 1) * 100 / max_z)
        slicer.app.processEvents()
        
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
    displayNode.SetWindow(float(slices))
    displayNode.SetLevel(float(slices + 1) / 2.0)
    displayNode.SetInterpolate(0)
    
    logging.info('Processing completed %d %d' % (imageData.GetScalarRange()[0], imageData.GetScalarRange()[1]))

    return True


class LabelMapAPSliceTest(ScriptedLoadableModuleTest):
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
    self.test_LabelMapAPSlice1()

  def test_LabelMapAPSlice1(self):
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
