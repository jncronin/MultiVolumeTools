import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy

#
# LabelStatisticsPerSlice
#

class LabelStatisticsPerSlice(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LabelStatisticsPerSlice" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MultiVolumeTools"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Cronin (KCL)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Performs LabelStatistics on a slice-by-slice basis 
    """
    self.parent.acknowledgementText = """
    By John Cronin.
""" # replace with organization, grant and thanks.

#
# LabelStatisticsPerSliceWidget
#

class LabelStatisticsPerSliceWidget(ScriptedLoadableModuleWidget):
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
	
    # output volume template
    #
    self.lmap = slicer.qMRMLNodeComboBox()
    self.lmap.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.lmap.selectNodeUponCreation = True
    self.lmap.addEnabled = False
    self.lmap.removeEnabled = False
    self.lmap.noneEnabled = False
    self.lmap.renameEnabled = False
    self.lmap.showHidden = False
    self.lmap.showChildNodeTypes = False
    self.lmap.setMRMLScene( slicer.mrmlScene )
    self.lmap.setToolTip( "Pick the input label map." )
    parametersFormLayout.addRow("Label Map: ", self.lmap)
    
    self.long = qt.QCheckBox()
    self.long.setChecked(True)
    parametersFormLayout.addRow("Long table output: ", self.long)

    self.whole = qt.QCheckBox()
    self.whole.setChecked(False)
    parametersFormLayout.addRow("Whole volume: ", self.whole)

    self.sm = qt.QLineEdit()
    self.sm.text = '0'
    parametersFormLayout.addRow("Slice Modulo: ", self.sm)
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Add to output")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)
    
    #
    # Clear output button
    #
    self.clearButton = qt.QPushButton("Clear Output")
    self.clearButton.toolTip = "Clear output table"
    self.clearButton.enabled = True
    parametersFormLayout.addRow(self.clearButton)

    # Special JC version to automate things
    self.jcbutton = qt.QPushButton("AutoJC")
    self.jcbutton.enabled = True
    parametersFormLayout.addRow(self.jcbutton)
    	
    # Run analysis on all combinations of label and volume maps
    self.allbutton = qt.QPushButton("Run on all")
    self.allbutton.enabled = True
    parametersFormLayout.addRow(self.allbutton)    	

    #
    # Progress Bar
    #
    self.progbar = qt.QProgressBar()
    self.progbar.setValue(0)
    parametersFormLayout.addRow(self.progbar)

    # Add vertical spacer
    #self.layout.addStretch(1)
    
    #
    # Output Area
    #
    outputCollapsibleButton = ctk.ctkCollapsibleButton()
    outputCollapsibleButton.text = "Output"
    self.layout.addWidget(outputCollapsibleButton)

    # Layout within the dummy collapsible button
    outputFormLayout = qt.QFormLayout(outputCollapsibleButton)
    
    # Output table
    self.tw = qt.QTableWidget()
    outputFormLayout.addRow(self.tw)
    
    #
    # Save output button
    #
    self.saveButton = qt.QPushButton("Save Output As")
    self.saveButton.toolTip = "Save output table"
    self.saveButton.enabled = True
    outputFormLayout.addRow(self.saveButton)

    
    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.clearButton.connect('clicked(bool)', self.onClearButton)
    self.saveButton.connect('clicked(bool)', self.onSaveButton)
    self.jcbutton.connect('clicked(bool)', self.onJCButton)
    self.allbutton.connect('clicked(bool)', self.onAll)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.lmap.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    
    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onJCButton(self):
    self.tw.setRowCount(0)
    self.tw.setColumnCount(0)

    logic = LabelStatisticsPerSliceLogic()
    
    myorder = [ [ 'x', 'm-label' ],
                [ 'y', 'm-label' ],
                [ 'z', 'm-label' ],
                [ 'm', 'm-label' ],
                [ 'x', 'ap3' ],
                [ 'y', 'ap3' ],
                [ 'z', 'ap3' ],
                [ 'm', 'ap3' ],
                [ 'y', 'fam' ] ]
    
    for curorder in myorder:
      try:
        logic.run(slicer.util.getNode(curorder[0]), slicer.util.getNode(curorder[1]), self.progbar, self.tw, self.long.isChecked(), self.whole.isChecked(), int(self.sm.text))
      except Exception:
        pass

  def onAll(self):
    logic = LabelStatisticsPerSliceLogic()

    # get all volume nodes and label maps
    d = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')

    print(d)
    vns = filter(lambda x: x.IsA('vtkMRMLLabelMapVolumeNode')==0, d)
    lms = filter(lambda x: x.IsA('vtkMRMLLabelMapVolumeNode')==1, d)

    for vn in vns:
      for lm in lms:
        if vn.GetOrigin() == lm.GetOrigin() and vn.GetSpacing() == lm.GetSpacing() and vn.GetImageData().GetDimensions() == lm.GetImageData().GetDimensions():
          print(vn.GetName() + "/" + lm.GetName())
          logic.run(vn, lm, self.progbar, self.tw, self.long.isChecked(), self.whole.isChecked(), int(self.sm.text))
  
  def onSelect(self):
    self.applyButton.enabled = (self.inputSelector.currentNode() is not None) & (self.lmap.currentNode() is not None)

  def onApplyButton(self):
    logic = LabelStatisticsPerSliceLogic()
    logic.run(self.inputSelector.currentNode(), self.lmap.currentNode(), self.progbar, self.tw, self.long.isChecked(), self.whole.isChecked(), int(self.sm.text))
    
  def onClearButton(self):
    self.tw.setRowCount(0)
    self.tw.setColumnCount(0)
    
  def onSaveButton(self):
    # file picker
    qfd = qt.QFileDialog()
    qfd.windowTitle = 'Save Output As'
    qfd.modal = True

    # newer Qt changes filter semantics
    try:
      qfd.setFilter('Comma-separated values (*.csv)')
    except ValueError:
      qfd.setNameFilter('Comma-separated values (*.csv)')
    
    qfd.acceptMode = qt.QFileDialog.AcceptSave
    qfd.fileMode = qt.QFileDialog.AnyFile
    qfd.defaultSuffix = 'csv'
    
    if qfd.exec_() == qt.QFileDialog.AcceptSave:
      fname = qfd.selectedFiles()[0]
      # saving logic
      tw = self.tw
      f = open(fname, 'w')
      
      for x in range(0, tw.columnCount):
        if x != 0:
          f.write(',')
        f.write(tw.horizontalHeaderItem(x).text())
      f.write('\n')
      
      for y in range(0, tw.rowCount):
        for x in range(0, tw.columnCount):
          if x != 0:
            f.write(',')
          twi = tw.item(y,x)
          if twi is not None:
            f.write(tw.item(y,x).text())
        f.write('\n')
      
      f.close()
    
#
# pig_dynLogic
#

class LabelStatisticsPerSliceLogic(ScriptedLoadableModuleLogic):
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

  def run(self, input_vol, lmap, pb = None, tw = None, long = True, whole = False, slice_modulo = 1):
    """
    Run the actual algorithm
    """

    if input_vol is None or lmap is None:
      return

    logging.info('Processing started')
    
    import vtk.util.numpy_support
    input_im = input_vol.GetImageData()
    input_shape = list(input_im.GetDimensions())
    input_shape.reverse()
    a = vtk.util.numpy_support.vtk_to_numpy(input_im.GetPointData().GetScalars()).reshape(input_shape)
    
    import vtk.util.numpy_support
    lm_im = lmap.GetImageData()
    lm_shape = list(input_im.GetDimensions())
    lm_shape.reverse()
    b = vtk.util.numpy_support.vtk_to_numpy(lm_im.GetPointData().GetScalars()).reshape(lm_shape)

    counts = []
    means = []
    vols = []
    sds = []
    medians = []
    Rs = []
    As = []
    Ss = []
    slice_counts = []
    zones = int(lm_im.GetScalarRange()[1])
    print('%d zones' % zones)
    
    max_z = input_shape[0]
    max_y = input_shape[1]
    max_x = input_shape[2]
    
    spacing = input_vol.GetSpacing()
    voxel_size = spacing[0] * spacing[1] * spacing[2]

    ras_matrix = vtk.vtkMatrix4x4()
    input_vol.GetRASToIJKMatrix(ras_matrix)
    ijk_matrix = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Invert(ras_matrix, ijk_matrix)

    if whole:
      corr_z = [range(0, max_z)]
    elif slice_modulo > 0:
      corr_z = [range(0,max_z)[x::slice_modulo] for x in range(0, slice_modulo)]
    else:
      corr_z = [[x] for x in range(0, max_z)]

    if pb is None:
      pass
    else:
      pb.setValue(0)
      slicer.app.processEvents()
              
    for zidx in range(0, len(corr_z)):
      z = corr_z[zidx]

      cur_counts = []
      cur_means = []
      cur_sd = []
      cur_medians = []
      cur_Rs = []
      cur_As = []
      cur_Ss = []
      cur_slice_counts = []
      
      if whole:
        vz = a
        lz = b
      else:
        vz = a[z]
        lz = b[z]
      
      for t in range(1, zones+1):
        vzone = vz[lz == t]
        cur_counts.append(len(vzone))

        # Used to generate RAS coordinates from IJK ones
        pin = [ 0.0, 0.0, numpy.mean(z), 1.0 ]
        pout = [ 0.0, 0.0, 0.0, 0.0 ]
        
        if(len(vzone) > 0):
          cur_means.append(numpy.mean(vzone))
          cur_sd.append(numpy.std(vzone))
          cur_medians.append(numpy.median(vzone))

          # find centroid of i,j values
          vidx = numpy.where(lz == t)
          vidx_dims = numpy.shape(vidx)[0]

          pin[1] = sum(vidx[vidx_dims - 2]) / len(vidx[vidx_dims - 2])
          pin[0] = sum(vidx[vidx_dims - 1]) / len(vidx[vidx_dims - 1])

          if whole:
            pin[2] = sum(vidx[vidx_dims - 3]) / len(vidx[vidx_dims - 3])
            print(vidx[vidx_dims - 3])
        else:
          cur_means.append(0)
          cur_sd.append(0)

        # Generate RAS coords
        ijk_matrix.MultiplyPoint(pin, pout)
        cur_Rs.append(pout[0])
        cur_As.append(pout[1])
        cur_Ss.append(pout[2])

        # number of slices in current entry
        cur_slice_counts.append(len(z))
      
      cur_vols = [x * voxel_size / 1000.0 for x in cur_counts]
      
      counts.append(cur_counts)
      means.append(cur_means)
      vols.append(cur_vols)
      sds.append(cur_sd)
      medians.append(cur_medians)
      Rs.append(cur_Rs)
      As.append(cur_As)
      Ss.append(cur_Ss)
      slice_counts.append(cur_slice_counts)
               
      logging.info('Processed frame %d' % zidx)
	  
      if pb is None:
        pass
      else:
        pb.setValue((zidx + 1) * 100 / len(corr_z))
        slicer.app.processEvents()
    
    logging.info('Processing completed')

    max_z = len(corr_z)
    
    if (tw is not None):
      if long == True:
        # print in long tabular form
        cur_row = tw.rowCount
        cur_col = tw.columnCount
        new_col = 12
        
        if(new_col > cur_col):
          tw.setColumnCount(new_col)
          headers = []
          headers.append('input_vol')
          headers.append('label_map')
          headers.append('zone')
          headers.append('count')
          headers.append('vol')
          headers.append('mean')
          headers.append('sd')
          headers.append('median')
          headers.append('R')
          headers.append('A')
          headers.append('S')
          headers.append('slice_count')
          tw.setHorizontalHeaderLabels(headers)
      
        tw.setRowCount(max_z * zones + cur_row)

        for z in range(0, len(corr_z)):
          for zone in range(0, zones):
            tw.setItem(z * zones + zone + cur_row, 0, qt.QTableWidgetItem(input_vol.GetName()))
            tw.setItem(z * zones + zone + cur_row, 1, qt.QTableWidgetItem(lmap.GetName()))
            tw.setItem(z * zones + zone + cur_row, 2, qt.QTableWidgetItem('%d' % zone))
            tw.setItem(z * zones + zone + cur_row, 3, qt.QTableWidgetItem('%d' % counts[z][zone]))
            tw.setItem(z * zones + zone + cur_row, 4, qt.QTableWidgetItem('%.3g' % vols[z][zone]))

            # handle count == 0 as NA
            if counts[z][zone] == 0:
              tw.setItem(z * zones + zone + cur_row, 5, qt.QTableWidgetItem('NA'))
              tw.setItem(z * zones + zone + cur_row, 6, qt.QTableWidgetItem('NA'))
              tw.setItem(z * zones + zone + cur_row, 7, qt.QTableWidgetItem('NA'))
              tw.setItem(z * zones + zone + cur_row, 8, qt.QTableWidgetItem('NA'))
              tw.setItem(z * zones + zone + cur_row, 9, qt.QTableWidgetItem('NA'))
              tw.setItem(z * zones + zone + cur_row, 10, qt.QTableWidgetItem('NA'))
            else:
              tw.setItem(z * zones + zone + cur_row, 5, qt.QTableWidgetItem('%.3g' % means[z][zone]))
              tw.setItem(z * zones + zone + cur_row, 6, qt.QTableWidgetItem('%.3g' % sds[z][zone]))
              tw.setItem(z * zones + zone + cur_row, 7, qt.QTableWidgetItem('%.3g' % medians[z][zone]))
              tw.setItem(z * zones + zone + cur_row, 8, qt.QTableWidgetItem('%.3g' % Rs[z][zone]))
              tw.setItem(z * zones + zone + cur_row, 9, qt.QTableWidgetItem('%.3g' % As[z][zone]))
              tw.setItem(z * zones + zone + cur_row, 10, qt.QTableWidgetItem('%.3g' % Ss[z][zone]))
            
            tw.setItem(z * zones + zone + cur_row, 11, qt.QTableWidgetItem('%d' % slice_counts[z][zone]))

      else:
        # print in wide tabular form
      
        cur_row = tw.rowCount
        cur_col = tw.columnCount
        new_col = zones * 9 + 2
        
        if(new_col > cur_col):
          tw.setColumnCount(new_col)
          headers = []
          headers.append('input_vol')
          headers.append('label_map')
          for zone in range(0, zones):
            headers.append('z%d_count' % zone)
            headers.append('z%d_vol' % zone)
            headers.append('z%d_mean' % zone)
            headers.append('z%d_sd' % zone)
            headers.append('z%d_median' % zone)
            headers.append('z%d_R' % zone)
            headers.append('z%d_A' % zone)
            headers.append('z%d_S' % zone)
            headers.append('z%d_slice_count' % zone)
          tw.setHorizontalHeaderLabels(headers)
        
        tw.setRowCount(max_z + cur_row)      
        
        for z in range(0, len(corr_z)):
          twiv = qt.QTableWidgetItem(input_vol.GetName())
          twlm = qt.QTableWidgetItem(lmap.GetName())
          tw.setItem(z + cur_row, 0, twiv)
          tw.setItem(z + cur_row, 1, twlm)
          for zone in range(0, zones):
            twic = qt.QTableWidgetItem('%d' % counts[z][zone])
            twivol = qt.QTableWidgetItem('%.3g' % vols[z][zone])
            twim = qt.QTableWidgetItem('%.3g' % means[z][zone])
            twisd = qt.QTableWidgetItem('%.3g' % sds[z][zone])
            twimed = qt.QTableWidgetItem('%.3g' % medians[z][zone])
            tw.setItem(z + cur_row, zone * 9 + 2, twic)
            tw.setItem(z + cur_row, zone * 9 + 3, twivol)
            tw.setItem(z + cur_row, zone * 9 + 4, twim)
            tw.setItem(z + cur_row, zone * 9 + 5, twisd)
            tw.setItem(z + cur_row, zone * 9 + 6, twimed)
            tw.setItem(z + cur_row, zone * 9 + 7, qt.QTableWidgetItem('%.3g' % Rs[z][zone]))
            tw.setItem(z + cur_row, zone * 9 + 8, qt.QTableWidgetItem('%.3g' % As[z][zone]))
            tw.setItem(z + cur_row, zone * 9 + 9, qt.QTableWidgetItem('%.3g' % Ss[z][zone]))
            tw.setItem(z + cur_row, zone * 9 + 10, qt.QTableWidgetItem('%d' % slice_counts[z][zone]))

    return True


class LabelStatisticsPerSliceTest(ScriptedLoadableModuleTest):
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
    self.test_LabelStatisticsPerSlice1()

  def test_LabelStatisticsPerSlice1(self):
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
