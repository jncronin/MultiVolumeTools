import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# RASToPointData
#

class RASToPointData(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "RASToPointData" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Generate a volume containing 3xfloats with each data point equal to its RAS coordinates
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# RASToPointDataWidget
#

class RASToPointDataWidget(ScriptedLoadableModuleWidget):
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
    self.inputSelector.setToolTip( "Input volume." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    # output volume
    self.ovol = slicer.qMRMLNodeComboBox()
    self.ovol.nodeTypes = ["vtkMRMLVectorVolumeNode"]
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
    logic = RASToPointDataLogic()
    logic.run(self.inputSelector.currentNode(), self.ovol.currentNode(), self.progbar)

#
# pig_dynLogic
#

class RASToPointDataLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, input_vol, output_vol, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_im = input_vol.GetImageData()
    input_shape = list(input_im.GetDimensions())


    # determine new image size
    output_shape = input_shape
    output_shape.reverse()
    output_shape.append(3)

    od = vtk.vtkImageData()
    od.SetDimensions(input_im.GetDimensions())
    od.AllocateScalars(vtk.VTK_FLOAT, 3)

    oscal = od.GetPointData().GetScalars()

    da = vtk.util.numpy_support.vtk_to_numpy(oscal).reshape(output_shape)

    # algorithm - TODO
    #for z in range(0, output_shape[0]):
    #  for y in range(0, output_shape[1]):
    #    for x in range(0, output_shape[2]):
    #      da[z, y, x, 0] = x
    #      da[z, y, x, 1] = y
    #      da[z, y, x, 2] = z
    #if pb is None:
    #  pass
    #else:
    #  pb.setValue(z / output_shape[0] * 100)
    #  slicer.app.processEvents()

    oi = np.indices(output_shape[0:3])

    # get IJK to RAS
    mtform = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASMatrix(mtform)

    # we can special case the situation where there is no rotation involved
    mtformnp = np.zeros(16)
    mtform.DeepCopy(mtformnp, mtform)
    tformtlate = np.array([1,0,0,1,0,1,0,1,0,0,1,1,0,0,0,1])
    if np.array_equal(tformtlate * mtformnp, mtformnp):
      dirs = np.zeros([3,3])  # guaranteed to be pure scale
      input_vol.GetIJKToRASDirections(dirs)
      spac = input_vol.GetSpacing()
      origs = input_vol.GetOrigin()

      z = oi[0] * dirs[2,2] * spac[2] + origs[2]
      y = oi[1] * dirs[1,1] * spac[1] + origs[1]
      x = oi[2] * dirs[0,0] * spac[0] + origs[0]

      oras = np.stack((x,y,z), axis=-1)
    else:
      print("Rotation involved, not yet implemented")

      #ois = np.stack((oi[2], oi[1], oi[0]), axis=-1)

      #def ijktoras(a):
      #  return mtform.MultiplyPoint(np.append(a, 1))[0:3]
      
      #oras = np.apply_along_axis(ijktoras, 3, ois)
      oras = np.stack((oi[2], oi[1], oi[0]), axis=-1)

    da[:] = oras
    

    # add data to output node
    volumeNode = output_vol
    volumeNode.SetSpacing(input_vol.GetSpacing())
    volumeNode.SetOrigin(input_vol.GetOrigin())



    #vl = slicer.modules.volumes.logic()
	
    #if pb is None:
    #  pass
    #else:
    #  pb.setValue(0)
    #  slicer.app.processEvents()
         
    #imageSize=[new_x, new_y, new_z]
    #voxelType=input_vol.GetImageData().GetScalarType()
    # Create an empty image volume
    #imageData=vtk.vtkImageData()
    #imageData.DeepCopy(input_vol.GetImageData())
    #imageData.SetDimensions(new_x, new_y, new_z)
    #imageData.AllocateScalars(vtk.VTK_FLOAT, 1)

    #output_scalars = imageData.GetPointData().GetScalars()
    #da = vtk.util.numpy_support.vtk_to_numpy(output_scalars).reshape(output_shape)
    #da = slicer.util.array(volumeNode.GetID())


       
    od.Modified()
    oscal.Modified()
    
    thresholder=vtk.vtkImageThreshold()
    thresholder.SetInputData(od)
    thresholder.Update()
    #thresholder.SetInValue(0)
    #thresholder.SetOutValue(0)
    # Create volume node
    vm = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASDirectionMatrix(vm)
    volumeNode.SetIJKToRASDirectionMatrix(vm)
    volumeNode.SetImageDataConnection(thresholder.GetOutputPort())

    # Add volume to scene
    displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    volumeNode.CreateDefaultStorageNode()
    
    logging.info('Processing completed')
    if pb is None:
      pass
    else:
      pb.setValue(100)
      slicer.app.processEvents()

    # Assign to slice viewers
    #slicer.util.setSliceViewerLayers(background=input_vol, foreground=output_vol, foregroundOpacity=0.5)
    #for sliceViewName in slicer.app.layoutManager().sliceViewNames():
    # sw = slicer.app.layoutManager().sliceWidget(sliceViewName)
    # sw.sliceLogic().FitSliceToAll()

    return True


class RASToPointDataTest(ScriptedLoadableModuleTest):
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
    self.test_RASToPointData1()

  def test_RASToPointData1(self):
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
