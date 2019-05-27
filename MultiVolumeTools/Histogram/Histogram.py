import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# Histogram
#

class Histogram(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Histogram" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Generate histogram in CSV format.  Optionally mask the input with a label map.
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.
    self.logic = HistogramLogic()

#
# HistogramWidget
#

class HistogramWidget(ScriptedLoadableModuleWidget):
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

    # range/bins selector
    self.range_min = qt.QLineEdit()
    self.range_min.text = '0.0'
    parametersFormLayout.addRow("Min: ", self.range_min)
    self.range_max = qt.QLineEdit()
    self.range_max.text = '1.0'
    parametersFormLayout.addRow("Max: ", self.range_max)
    self.bins = qt.QLineEdit()
    self.bins.text = '500'
    parametersFormLayout.addRow("Bins: ", self.bins)

    self.byframe_box = qt.QCheckBox()
    self.byframe_box.setChecked(False)
    parametersFormLayout.addRow("By Frame: ", self.byframe_box)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Save to CSV")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)
    	
    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None)
    if self.inputSelector.currentNode() is not None:
      im = self.inputSelector.currentNode().GetImageData()
      if im is not None:
        rng = im.GetScalarRange()
        self.range_min.text = '%.3f' % rng[0]
        self.range_max.text = '%.3f' % rng[1]

  
  def onApplyButton(self):
    # file picker
    qfd = qt.QFileDialog()
    qfd.windowTitle = 'Save Output As'
    qfd.modal = True
    qfd.setFilter('Comma-separated values (*.csv)')
    qfd.acceptMode = qt.QFileDialog.AcceptSave
    qfd.fileMode = qt.QFileDialog.AnyFile
    qfd.defaultSuffix = 'csv'
    qfd.selectFile('hist.csv')
    
    if qfd.exec_() == qt.QFileDialog.AcceptSave:
      fname = qfd.selectedFiles()[0]      
      logic = HistogramLogic()
      logic.run(self.inputSelector.currentNode(), self.imask.currentNode(), fname=fname, binrange=(float(self.range_min.text), float(self.range_max.text)), bins=int(self.bins.text), byframe=self.byframe_box.isChecked())

#
# pig_dynLogic
#

class HistogramLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, input_vol, input_mask, fname = "/tmp/out.csv", binrange = None, bins = 100, byframe = False):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_im = input_vol.GetImageData()
    input_shape = list(input_im.GetDimensions())
    input_shape.reverse()
    a = vtk.util.numpy_support.vtk_to_numpy(input_im.GetPointData().GetScalars()).reshape(input_shape)
    max_z = input_shape[0]

    if(binrange is None):
      binrange = (np.min(a), np.max(a))
    
    if(input_mask is not None):
      input_imask = input_mask.GetImageData()
      b = vtk.util.numpy_support.vtk_to_numpy(input_imask.GetPointData().GetScalars()).reshape(input_shape)

    if byframe:
      corr_z = [[x] for x in range(0, max_z)]
    else:
      corr_z = [range(0, max_z)]
    
    f = open(fname, 'w')
    f.write('frame,bin_start,bin_mid,bin_end,count,density\n')

    for zidx in range(0, len(corr_z)):
      z = corr_z[zidx]

      cur_a = a[z]
      
      if input_mask is not None:
        cur_b = b[z]
        cur_a = cur_a[np.where(cur_b != 0)]

      hist = np.histogram(cur_a, bins=bins, range=binrange)
      tot_range = hist[1][len(hist[1])-1] - hist[1][0]
      bin_width = tot_range / len(hist[0])
      bin_starts = hist[1][0:len(hist[0])]
      bin_mids = bin_starts + bin_width / 2
      bin_ends = bin_starts + bin_width

      csum = np.sum(hist[0])
      if csum == 0:
        densities = np.zeros_like(hist[0])
      else:
        densities = hist[0].astype(float) / np.sum(hist[0])
    
      for x in xrange(0, len(hist[0])):
        f.write('%d,%f,%f,%f,%d,%f\n' % (zidx, bin_starts[x], bin_mids[x], bin_ends[x], hist[0][x], densities[x]))
    
    f.close()

    logging.info('Processing complete')
    
    return True


class HistogramTest(ScriptedLoadableModuleTest):
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
    self.test_Histogram1()

  def test_Histogram1(self):
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
