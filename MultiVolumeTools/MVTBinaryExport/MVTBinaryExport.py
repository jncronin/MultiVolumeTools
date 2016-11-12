import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from struct import pack
import logging

#
# MVTBinaryExport
#

class MVTBinaryExport(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MVTBinaryExport" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Export a Volume to a simple binary format.  Designed 
    to interface with MVTConvert as it preserves metadata.
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# MVTBinaryExport_exportWidget
#

class MVTBinaryExport_exportWidget(ScriptedLoadableModuleWidget):
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
    
    #
    # input label volume selector
    #
    self.inputLabelSelector = slicer.qMRMLNodeComboBox()
    self.inputLabelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.inputLabelSelector.selectNodeUponCreation = True
    self.inputLabelSelector.addEnabled = False
    self.inputLabelSelector.removeEnabled = False
    self.inputLabelSelector.noneEnabled = False
    self.inputLabelSelector.showHidden = False
    self.inputLabelSelector.showChildNodeTypes = False
    self.inputLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.inputLabelSelector.setToolTip( "Pick the input label map to the algorithm." )
    parametersFormLayout.addRow("Input Label Map: ", self.inputLabelSelector)

    self.fname = qt.QLineEdit()
    self.fname.text = '/tmp/analysis.bin'
    parametersFormLayout.addRow("Export to file: ", self.fname)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
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
    self.inputLabelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onLabelSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass
    
  def onLabelSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.inputLabelSelector.currentNode() is not None)

  def onSelect(self):
    input_vol = self.inputSelector.currentNode()
    if((input_vol is not None) & (input_vol.GetAttribute('pig_dyn.AcquisitionDateTime') is not None)):
      self.fname.text = '/tmp/analysis-' + input_vol.GetAttribute('pig_dyn.AcquisitionDateTime') + '.bin'
    self.onLabelSelect()

  def onApplyButton(self):
    logic = MVTBinaryExport_exportLogic()
    logic.run(self.inputSelector.currentNode(), self.inputLabelSelector.currentNode(), self.fname.text, self.progbar)

#
# MVTBinaryExport_exportLogic
#

class MVTBinaryExport_exportLogic(ScriptedLoadableModuleLogic):
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
    
  def write_string(self, ofile, str):
    if(str is not None):
      slen = len(str)
      ofile.write(pack('<h', slen))
      for c in str:
        ofile.write(c)
    else:
      ofile.write(pack('<h', 0))

  def run(self, input_vol, input_label_vol, fname, pb = None):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
      
    a = slicer.util.array(input_vol.GetName())
    lma = slicer.util.array(input_label_vol.GetName())
    max_z = len(a)
    max_y = len(a[0])
    max_x = len(a[0][0])
    
    imageSpacing=input_vol.GetSpacing()
    
    source_name = input_vol.GetAttribute('pig_dyn.SourceName')
    acquisition_datetime = input_vol.GetAttribute('pig_dyn.AcquisitionDateTime')
    series_name = input_vol.GetAttribute('pig_dyn.SeriesName')
    patient_name = input_vol.GetAttribute('pig_dyn.PatientName')
    
    ofile = open(fname, 'wb')
    ofile.write(pack('<ddd', imageSpacing[0], imageSpacing[1], imageSpacing[2]))
    ofile.write(pack('<iii', max_x, max_y, max_z - 2))
    
    self.write_string(ofile, source_name)
    self.write_string(ofile, acquisition_datetime)
    self.write_string(ofile, series_name)
    self.write_string(ofile, patient_name)
    
    for z in xrange(0, max_z):
      if(z == 0):
        pass
      elif(z == (max_z - 1)):
        pass
      else:
        for y in xrange(0, max_y):
          for x in xrange(0, max_x):
            if(lma[z][y][x] == 1):
              ofile.write(pack('<h', a[z][y][x]))
            else:
              ofile.write(pack('<h', -1001))
      
      if pb is None:
        pass
      else:
        pb.setValue(z * 100 / (max_z - 1))
        slicer.app.processEvents()

    ofile.close()
    logging.info('Processing completed')

    return True


class MVTBinaryExport_exportTest(ScriptedLoadableModuleTest):
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
    self.test_pig_dyn_export1()

  def test_pig_dyn_export1(self):
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
    logic = pig_dyn_exportLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
