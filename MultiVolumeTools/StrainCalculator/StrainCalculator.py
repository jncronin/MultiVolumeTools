import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# StrainCalculator
#

class StrainCalculator(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "StrainCalculator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Generate volumes containing the difference between two vector volumes in the x, y and z directions, along with absolute change (sqrt(x*x + y*y + z*z))
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# StrainCalculatorWidget
#

class StrainCalculatorWidget(ScriptedLoadableModuleWidget):
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
    self.inputSelector.setToolTip( "Input volume 1." )
    parametersFormLayout.addRow("Input Volume 1: ", self.inputSelector)

    self.inputSelector2 = slicer.qMRMLNodeComboBox()
    self.inputSelector2.nodeTypes = ["vtkMRMLVectorVolumeNode"]
    self.inputSelector2.selectNodeUponCreation = True
    self.inputSelector2.addEnabled = False
    self.inputSelector2.removeEnabled = False
    self.inputSelector2.noneEnabled = False
    self.inputSelector2.showHidden = False
    self.inputSelector2.showChildNodeTypes = False
    self.inputSelector2.setMRMLScene( slicer.mrmlScene )
    self.inputSelector2.setToolTip( "Input volume 2." )
    parametersFormLayout.addRow("Input Volume 2: ", self.inputSelector2)

    # output volumes
    self.ovolx = slicer.qMRMLNodeComboBox()
    self.ovolx.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.ovolx.selectNodeUponCreation = True
    self.ovolx.addEnabled = True
    self.ovolx.removeEnabled = False
    self.ovolx.noneEnabled = False
    self.ovolx.renameEnabled = True
    self.ovolx.showHidden = False
    self.ovolx.showChildNodeTypes = False
    self.ovolx.setMRMLScene( slicer.mrmlScene )
    self.ovolx.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output x Volume: ", self.ovolx)

    self.ovoly = slicer.qMRMLNodeComboBox()
    self.ovoly.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.ovoly.selectNodeUponCreation = True
    self.ovoly.addEnabled = True
    self.ovoly.removeEnabled = False
    self.ovoly.noneEnabled = False
    self.ovoly.renameEnabled = True
    self.ovoly.showHidden = False
    self.ovoly.showChildNodeTypes = False
    self.ovoly.setMRMLScene( slicer.mrmlScene )
    self.ovoly.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output y Volume: ", self.ovoly)

    self.ovolz = slicer.qMRMLNodeComboBox()
    self.ovolz.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.ovolz.selectNodeUponCreation = True
    self.ovolz.addEnabled = True
    self.ovolz.removeEnabled = False
    self.ovolz.noneEnabled = False
    self.ovolz.renameEnabled = True
    self.ovolz.showHidden = False
    self.ovolz.showChildNodeTypes = False
    self.ovolz.setMRMLScene( slicer.mrmlScene )
    self.ovolz.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output z Volume: ", self.ovolz)

    self.ovola = slicer.qMRMLNodeComboBox()
    self.ovola.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.ovola.selectNodeUponCreation = True
    self.ovola.addEnabled = True
    self.ovola.removeEnabled = False
    self.ovola.noneEnabled = False
    self.ovola.renameEnabled = True
    self.ovola.showHidden = False
    self.ovola.showChildNodeTypes = False
    self.ovola.setMRMLScene( slicer.mrmlScene )
    self.ovola.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output absolute Volume: ", self.ovola)
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
    self.inputSelector2.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ovolx.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ovoly.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ovolz.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ovola.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.inputSelector2 is not None) & ((self.ovola.currentNode() is not None) | (self.ovolx.currentNode() is not None) | (self.ovoly.currentNode() is not None) | (self.ovolz.currentNode() is not None))

  def onApplyButton(self):
    logic = StrainCalculatorLogic()
    logic.run(self.inputSelector.currentNode(), self.inputSelector2.currentNode(), self.ovolx.currentNode(), self.ovoly.currentNode(), self.ovolz.currentNode(), self.ovola.currentNode(), self.progbar)

#
# pig_dynLogic
#

class StrainCalculatorLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, ivol1, ivol2, ovolx, ovoly, ovolz, ovola, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_ima = ivol1.GetImageData()
    input_shapea = list(input_ima.GetDimensions())
    input_shapea.reverse()
    a = vtk.util.numpy_support.vtk_to_numpy(input_ima.GetPointData().GetScalars()).reshape(input_shapea + [3])

    input_imb = ivol2.GetImageData()
    input_shapeb = list(input_imb.GetDimensions())
    input_shapeb.reverse()
    b = vtk.util.numpy_support.vtk_to_numpy(input_imb.GetPointData().GetScalars()).reshape(input_shapeb + [3])

    ax = a[:,:,:,0]
    ay = a[:,:,:,1]
    az = a[:,:,:,2]
    bx = b[:,:,:,0]
    by = b[:,:,:,1]
    bz = b[:,:,:,2]

    axd = np.diff(ax, axis=2, append=0)
    ayd = np.diff(ay, axis=1, append=0)
    azd = np.diff(az, axis=0, append=0)
    bxd = np.diff(bx, axis=2, append=0)
    byd = np.diff(by, axis=1, append=0)
    bzd = np.diff(bz, axis=0, append=0)


    dx = axd/bxd
    dy = ayd/byd
    dz = azd/bzd

    # set to output
    vm = vtk.vtkMatrix4x4()
    ivol1.GetIJKToRASDirectionMatrix(vm)

    # tuples of output volume and data to put in them (prevents code duplication)
    ovoldata = ( (ovolx, dx[:] - 1), (ovoly, dy[:] - 1), (ovolz, dz[:] - 1), (ovola, dx * dy * dz - 1) )

    for ovd in ovoldata:
      ovol = ovd[0]

      if ovd is not None:
        id = vtk.vtkImageData()
        id.SetDimensions(input_ima.GetDimensions())
        id.AllocateScalars(vtk.VTK_FLOAT, 1)

        osc = id.GetPointData().GetScalars()
        da = vtk.util.numpy_support.vtk_to_numpy(osc).reshape(input_shapea)

        da[:] = ovd[1]

        id.Modified()
        osc.Modified()

        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputData(id)
        thresholder.Update()

        ovol.SetSpacing(ivol1.GetSpacing())
        ovol.SetOrigin(ivol1.GetOrigin())
        ovol.SetIJKToRASDirectionMatrix(vm)

        ovol.SetImageDataConnection(thresholder.GetOutputPort())

        colorNode = slicer.util.getNode('ColdToHotRainbow')

        # window level excluding edges
        qtiles = np.quantile(da, (0.01, 0.99))
        w = qtiles[1] - qtiles[0]
        l = (qtiles[0] + qtiles[1]) / 2

        # Add volume to scene
        displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        ovol.SetAndObserveDisplayNodeID(displayNode.GetID())
        displayNode.SetAutoWindowLevel(0)
        displayNode.SetWindow(w)
        displayNode.SetLevel(l)


        ovol.CreateDefaultStorageNode()
        
    return True


class StrainCalculatorTest(ScriptedLoadableModuleTest):
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
    self.test_StrainCalculator1()

  def test_StrainCalculator1(self):
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
