import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
from math import ceil

#
# CPPPlanes
#

class CPPPlanes(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Control Point Plane Generator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Generate label maps describing a particular infero-superior plane in the .
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# CPPPlanesWidget
#

class CPPPlanesWidget(ScriptedLoadableModuleWidget):
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
    # Label map containing what moves into a particular slice
    self.lm = slicer.qMRMLNodeComboBox()
    self.lm.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.lm.selectNodeUponCreation = True
    self.lm.addEnabled = True
    self.lm.removeEnabled = False
    self.lm.noneEnabled = True
    self.lm.renameEnabled = True
    self.lm.showHidden = False
    self.lm.showChildNodeTypes = False
    self.lm.setMRMLScene( slicer.mrmlScene )
    self.lm.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Moving Label Map Volume: ", self.lm)

    # Label map containing what original slice
    self.lm2 = slicer.qMRMLNodeComboBox()
    self.lm2.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.lm2.selectNodeUponCreation = True
    self.lm2.addEnabled = True
    self.lm2.removeEnabled = False
    self.lm2.noneEnabled = True
    self.lm2.renameEnabled = True
    self.lm2.showHidden = False
    self.lm2.showChildNodeTypes = False
    self.lm2.setMRMLScene( slicer.mrmlScene )
    self.lm2.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Original Label Map Volume: ", self.lm2)

    # Numeric params
    self.level = qt.QLineEdit()
    self.level.text = '0'
    parametersFormLayout.addRow("Slice level in supero-inferior coordinates: ", self.level)

    self.tol = qt.QLineEdit()
    self.tol.text = '2.5'
    parametersFormLayout.addRow("Slice tolerance (1/2 width) in mm: ", self.tol)



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
    self.lm.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.lm2.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & ((self.lm.currentNode() is not None) | (self.lm2.currentNode() is not None))

  def onApplyButton(self):
    logic = CPPPlanesLogic()
    logic.run(self.inputSelector.currentNode(), self.lm.currentNode(), self.lm2.currentNode(), float(self.level.text), float(self.tol.text), pb=self.progbar)

#
# pig_dynLogic
#

class CPPPlanesLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, input_vol, lmoving, lorig, level = -192.1, tol=2.5, pb = None):
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

    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
         
    imageSize=[max_x, max_y, max_z]

    vm = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASDirectionMatrix(vm)
    vm2 = vtk.vtkMatrix4x4()
    input_vol.GetIJKToRASMatrix(vm2)
    vm2.Invert()

    colorNode = slicer.util.getNode('GenericAnatomyColors')

    if lmoving is not None:
      imageDataLM=vtk.vtkImageData()
      imageDataLM.SetDimensions(max_x, max_y, max_z)
      imageDataLM.AllocateScalars(vtk.VTK_INT, 1)

      output_scalarsLM = imageDataLM.GetPointData().GetScalars()
      dlm = vtk.util.numpy_support.vtk_to_numpy(output_scalarsLM).reshape([max_z, max_y, max_x])

      dlm[:,:,:] = 0
      isdata = idata[:,:,:,2]
      dlm[np.where((isdata >= (level - tol)) & (isdata < (level + tol)))] = 1

      imageDataLM.Modified()
      output_scalarsLM.Modified()
      
      thresholderLM=vtk.vtkImageThreshold()
      thresholderLM.SetInputData(imageDataLM)
      thresholderLM.Update()

      lmoving.SetSpacing(imageSpacing)
      lmoving.SetOrigin(input_vol.GetOrigin())

      lmoving.SetIJKToRASDirectionMatrix(vm)

      lmoving.SetImageDataConnection(thresholderLM.GetOutputPort())

      displayNodeLM=slicer.vtkMRMLLabelMapVolumeDisplayNode()
      slicer.mrmlScene.AddNode(displayNodeLM)
      displayNodeLM.SetAndObserveColorNodeID(colorNode.GetID())
      lmoving.SetAndObserveDisplayNodeID(displayNodeLM.GetID())
      lmoving.CreateDefaultStorageNode()

    if lorig is not None:
      imageDataLOrig=vtk.vtkImageData()
      imageDataLOrig.SetDimensions(max_x, max_y, max_z)
      imageDataLOrig.AllocateScalars(vtk.VTK_INT, 1)

      output_scalarsLOrig = imageDataLOrig.GetPointData().GetScalars()
      dlorig = vtk.util.numpy_support.vtk_to_numpy(output_scalarsLOrig).reshape([max_z, max_y, max_x])

      dlorig[:,:,:] = 0

      # get max and min k coords in ijk space that represent the IS level
      aras = [0.0, 0.0, level - tol, 1.0]
      bras = [0.0, 0.0, level + tol, 1.0]
      aijk = vm2.MultiplyPoint(aras)
      bijk = vm2.MultiplyPoint(bras)

      min_k = int(min(aijk[2], bijk[2]))
      max_k = int(ceil(max(aijk[2], bijk[2])))

      dlorig[min_k:max_k,:,:] = 1
      
      imageDataLOrig.Modified()
      output_scalarsLOrig.Modified()
      
      thresholderLOrig=vtk.vtkImageThreshold()
      thresholderLOrig.SetInputData(imageDataLOrig)
      thresholderLOrig.Update()

      lorig.SetSpacing(imageSpacing)
      lorig.SetOrigin(input_vol.GetOrigin())

      lorig.SetIJKToRASDirectionMatrix(vm)

      lorig.SetImageDataConnection(thresholderLOrig.GetOutputPort())

      displayNodeLOrig=slicer.vtkMRMLLabelMapVolumeDisplayNode()
      slicer.mrmlScene.AddNode(displayNodeLOrig)
      displayNodeLOrig.SetAndObserveColorNodeID(colorNode.GetID())
      lorig.SetAndObserveDisplayNodeID(displayNodeLOrig.GetID())
      lorig.CreateDefaultStorageNode()


    logging.info('Processing completed')
    if pb is None:
      pass
    else:
      pb.setValue(100)
      slicer.app.processEvents()

    # Assign to slice viewers
    slicer.util.setSliceViewerLayers(label=lmoving)
    for sliceViewName in slicer.app.layoutManager().sliceViewNames():
     sw = slicer.app.layoutManager().sliceWidget(sliceViewName)
     sw.sliceLogic().FitSliceToAll()

    return True


class CPPPlanesTest(ScriptedLoadableModuleTest):
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
    self.test_CPPPlanes1()

  def test_CPPPlanes1(self):
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
