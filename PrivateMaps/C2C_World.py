##############################################################################
##
## World.py
## Toffer90
## Blazenclaw (lake edits)
## 
##############################################################################
##
## Based on:
##
## PerfectMongoose_v3.1/v3.3.py (by LunarMongoose)
##
##############################################################################
##
## Earlier based on:
##
## PerfectWorld3_v2.lua (for Civ5)
##
##############################################################################
## Initialize
##############################################################################

from CvPythonExtensions import *
from array  import array
from random import random, uniform, randint, seed, shuffle, choice
from math import fmod, pi, e, cos, sin, sqrt
import sys, os, inspect, _winreg
import cPickle as pickle
import BugUtil, NaturalWonders

##############################################################################
## GLOBAL TUNING VARIABLES: Change these to customize the map results.
## Please enter sane values, otherwise things WILL break!
##############################################################################

class MapConstants:
	def __init__(self):
		print "Initializing MapConstants"
		# Percentage of land squares to be Hills.
		self.HillPercent = 0.26

		# Percentage of land squares to be Peaks.
		self.PeakPercent = 0.07

		#Hotter than this temperature will be considered deciduous forest, colder will
		#be evergreen forest.Temperatures range from coldest 0.0 to hottest 1.0.
		self.ForestTemp = 0.3

		#What temperature will be considered hot enough to be jungle. Temperatures range
		#from coldest 0.0 to hottest 1.0.
		self.JungleTemp = 0.6

		#The chance for ice in the water gets this much lower per plot away from the poles
		self.IceChanceMultiplier = 0.75

		#Sets the threshold for jungle rainfall by modifying the plains threshold by this factor.
		self.fWoodFactor = 1.6

		#This is the maximum chance for a tree to be placed when rainfall is above jungle level.
		#use a value between 0.0 and 1.0
		self.fWoodChance = 0.94

		#This variable adjusts the amount of bonuses on the map. Values above 1.0 will add bonus bonuses.
		#People often want lots of bonuses, and for those people, this variable is definately a bonus.
		self.fBonusMult = 1.0

		# fRiverThreshold is used to decide if enough water has accumulated to form a river.
		# A lower value creates more rivers over the entire map. It controls length, complexity and density of rivers.
		self.fRiverThreshold = 0.02

		# This value controls the number of deep ocean trenches per ocean map square.
		self.fTrenchesPercent = 0.006

		# This value controls how many lake tiles will be generated as a percent of land tiles; the actual number of land tiles will NOT
		# be impacted by any value here, so long as there is ocean on the map. 0.01 approximates Earth's irl ~1% lake-land ratio.
		self.fLakesPercent = 0.06

		# This value adds a multiplier onto the default iMaxLakeSize; makes larger, or smaller, lakes, without impacting how many total lake tiles exist.
		self.fMaxLakeSizeMod = 1.5

		# --- The following values should all be between 0 and 1 ---
		# Base size of added lake is iOceanMinAreaSize as defined in the CIV4WorldInfo.xml minus 1.
		# A random value between fLakeSizeMinPercent and 1.0 is multiplied to spawned lakesizes when fLakeSizeFactorPercent roll true.
		self.fLakeSizeMinPercent = 0.50
		# fLakeSizeFactorPercent controls the percentage of lakes that are affected by the fLakeSizeMinPercent.
		self.fLakeSizeFactorPercent = 0.50
		# These alter lake size by a provided multiplicative factor, based on underlying terrain.
		self.fHeatLakeFactor = 0.10 # Desert, dunes & salt flats.
		self.fColdLakeFactor = 0.25 # Tundra, permafrost & ice.
		self.fWetLakeFactor = 1.25 # Lush, marsh, & muddy.
		# This value sets the relative minimum altitude of lake depressions.
		# It is relative to fLandHeight. A value of zero means that lakes can appear as low as the maximum ocean height.
		self.fRelMinLakeAlt = 0.20
		# This normalizes the minimum factor a lake can be shrunk to from starting at a high altitude; related to fRelMinLakeAlt. 0 -> full range, 1-> no shrinkage.
		# Low altitude factors will also increase the liklihood for lakes to touch oceans, forming saltwater harbors and making the coastline 'rougher'
		self.fAltitudeMinFactor = 0.50
		# This normalizes the minimum factor a lake can be shrunk to from low rainfall on starting location. 0 -> full range, 1-> no shrinkage.
		# Effectively increases randomization of lakesizes when a low value is used.
		self.fRainMinFactor = 0.25
		# This modifies the shape of how lakes form. 1 creates longer, snake-like lakes while 0 makes all lakes circular as can be.
		self.fLakeEccentricity = 0.30

		# Percent of way to max lake size (as defined in the CIV4WorldInfo.xml minus 1) at which point there is a 50/50 chance for a lake
		# to be either fresh or salt water. See fBlurHarshness for full impact of size on salinity type.
		# Must be >= 0.0. If >1, larger bodies of water than iMaxLakeSize may be freshwater.
		self.fBlurOnset = 0.80
		# This adjusts the blurring between large freshwater lakes and saltwater seas (modified logistic growth rate). Must be >= 0.0, when >= 100 immediate cutoff.
		# 0.0 gives a 50/50 chance any body of water (sans largest) will be freshwater or ocean, regardless of fBlurOnset.
		# 1.0 gives a ~90% chance of correct type at twice the relative onset; e.g. if onset is 0.8, 90% of lakes at 0.4*iMaxLakeSize are fresh, and 1.6*iMaxLakeSize saltwater
		# 2.0 makes the blur happen twice faster, e.g. ~90% chance for right type at ~0.6 or 1.2, and so on so forth.
		# These values are also locally modified by terrain, e.g. salt flats adjacency increases saltwater odds significantly, high rainfall freshwater, etc.
		self.fBlurHarshness = 1.00

		# The chance that a floodplain may appear on a valid riverside. Between 0 and 1.
		self.fFloodplainChance = 0.5

		# The percent chance that an oasis may appear in a desert. A tile must be desert and
		# surrounded on all sides by desert.
		self.fOasisChance = 0.004

		# The percent chance that a cactus feature may appear in a desert. A tile must be desert and
		# surrounded on all sides by desert.
		self.fCactusChance = 0.01

		# Tropical, temperate and polar zones are defined from 0 to 1.
		# They are a pecentage length away from equator in both north and south direction.
		self.fTropicLat		= 0.20
		self.fTemperateLat	= 0.50 # Temperate zone spans from 0.20 to 0.80, but is used a bit differently than the other latitude values.
		self.fPolarLat		= 0.80
		#---These values are for evaluating starting locations
		#Coastal cities are important, how important is determined by this value.
		self.CoastalCityValueBonus = 1.6
		#River cities are important, how important is determined by this value.
		self.RiverCityValueBonus = 2.4
		#Hill cities are important, how important is determined by this value.
		self.HillCityValueBonus = 1.2

		#Below here are static defines. Changing these may break the script.
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		self.N  = 1
		self.S  = 2
		self.E  = 3
		self.W  = 4
		self.NE = 5
		self.NW = 6
		self.SE = 7
		self.SW = 8

		self.WATER	= 0
		self.LAND	= 1
		self.HILL	= 2
		self.PEAK	= 3

		self.TRENCH		 = 1
		self.TRENCH_POL	 = 2
		self.TRENCH_TROP = 3
		self.OCEAN		 = 4
		self.OCEAN_POL	 = 5
		self.OCEAN_TROP	 = 6
		#↓ These must keep their relative order to each other.
		self.SEA		= 7
		self.SEA_POL	= 8
		self.SEA_TROP	= 9
		self.SEA_DEEP	= 10
		self.SEA_DEEP_P	= 11
		self.SEA_DEEP_T	= 12
		self.COAST		= 13
		self.COAST_POL	= 14
		self.COAST_TROP	= 15
		#↑ ------------------
		self.LAKE_SHORE	= 16
		self.LAKE		= 17
		self.MARSH		= 18
		self.GRASS		= 19
		self.PLAINS		= 20
		self.DESERT		= 21
		self.TAIGA		= 22
		self.ICE		= 23
		self.SALT_FLATS	= 24
		self.DUNES		= 25
		self.SCRUB		= 26
		self.BARREN		= 27
		self.LUSH		= 28
		self.MUDDY		= 29
		self.TUNDRA		= 30
		self.FROST		= 31
		self.ROCKY		= 32
		self.ROCKY_ARID = 33
		self.ROCKY_COLD	= 34
		##############################################################################
		## Settings
		##############################################################################
		''' These are values that affect the elevation map,
		higher numbers give greater chaos and smaller features.
		TODO: Make "world age" setting that modifies these; 3 billion years old, 4 billion, 5 billion.'''
		self.fBaseFreq = 0.46
		self.fLacunarity = 1.58
		# Roughness boundaries; range: 0-1.
		self.fMinPersi = 0.6
		self.fMaxPersi = 0.8
		''' They are tricky variables, tweaking them is not easy, nor predictable.'''

		# These set the water temperature compression that creates the land/sea seasonal temperature differences that cause monsoon winds.
		self.minWaterTemp = 0.20
		self.maxWaterTemp = 0.60

		# Strength of geostrophic rainfall
		self.geostrophicFactor				= 3.0
		self.geostrophicLateralWindStrength = 0.6

		# Wind Zones
		self.NOZONE		= -1
		self.NPOLAR		= 0
		self.NTEMPERATE = 1
		self.NEQUATOR	= 2
		self.SEQUATOR	= 3
		self.STEMPERATE	= 4
		self.SPOLAR		= 5

		# Crazy rain tweaking variables. I wouldn't touch these if I were you.
		# Minimum amount of rain dropped by default before other factors add to the amount of rain dropped
		self.minimumRainCost = .01
		self.upLiftExponent  = 4
		self.fPolarRainBoost  = .20

		# These attenuation factors lower the altitude of the map edges. Value between 0 an 1.
		# Low factor means strong attenuation at the edge, attenuation dissipates for each plot in the range.
		# This is currently used to prevent large continents in the uninhabitable polar regions.
		self.northAttenuationFactor = .40
		self.northAttenuationRange	= .06
		self.southAttenuationFactor = .80
		self.southAttenuationRange	= .16
		# East/west attenuation is set to zero, but modded maps may have need for them.east west attenuation may be desired for flat maps. 
		self.eastAttenuationFactor	= .0
		self.eastAttenuationRange	= .0
		self.westAttenuationFactor	= .0
		self.westAttenuationRange	= .0

		##############################################################################
		## ClimateMap Settings
		##############################################################################

		# What temperature will be considered cold enough to be ice, tundra and taiga.
		# Temperatures range from coldest 0.0 to hottest 1.0.
		self.IceTemp		= 0.03
		self.PermaFrostTemp = 0.05
		self.TundraTemp 	= 0.08
		self.TaigaTemp		= 0.20
		# Coldest absolute temperature allowed to be Scrub, desert, dunes or salt flats.
		self.fScrubTemp = 0.6

		#How many land squares will be below desert rainfall threshold. In this case,
		#rain levels close to zero are very likely to be desert, while rain levels close
		#to the desert threshold will more likely be plains.
		self.SaltFlatsPercent	= 0.03
		self.DunesPercent		= 0.09
		self.DesertPercent		= 0.18
		self.ScrubPercent		= 0.25
		#Affects the amount of rocky terrain. Proportional, Range 0-1.
		self.fRockyPercent = 0.05

		#How many land squares will be below plains rainfall threshold. Rain levels close
		#to the desert threshold are likely to be plains, while those close to the plains
		#threshold are likely to be grassland.
		self.PlainsPercent		= 0.44
		self.GrasslandPercent	= 0.68
		self.LushPercent		= 0.84
		self.MuddyPercent		= 0.92


	def initInGameOptions(self):
		MAP = CyGlobalContext().getMap()
		# Hills & Peaks
		selectionID = MAP.getCustomMapOption(0)
		if not selectionID:
			self.HillPercent *= 0.50
		elif selectionID == 1:
			self.HillPercent *= 0.75
		elif selectionID == 3:
			self.HillPercent *= 1.25
		elif selectionID == 4:
			self.HillPercent *= 1.50
		# Peaks
		selectionID = MAP.getCustomMapOption(1)
		if not selectionID:
			self.HillPercent *= 0.50
		elif selectionID == 1:
			self.HillPercent *= 0.75
		elif selectionID == 3:
			self.HillPercent *= 1.25
		elif selectionID == 4:
			self.HillPercent *= 1.50
		# Landmass Type
		selectionID = MAP.getCustomMapOption(2)
		self.bDryland = False
		self.bPangea = False
		self.bEarthlike = False
		self.bArchipelago = False
		self.bWaterworld = False
		self.bAttenuate = True 
		if not selectionID:
			self.bDryland = True
			self.bAttenuate = False
		elif selectionID == 1:
			self.bPangea = True
			self.fBaseFreq *= 0.76
			self.northAttenuationFactor	= .2
			self.northAttenuationRange	= .16
			self.southAttenuationFactor	= .2
			self.southAttenuationRange	= .16
			self.eastAttenuationFactor	= .2
			self.eastAttenuationRange	= .24
			self.westAttenuationFactor	= .2
			self.westAttenuationRange	= .24
		elif selectionID == 2:
			self.bEarthlike = True
		elif selectionID == 3:
			self.bArchipelago = True
			self.fBaseFreq *=  1.8
			self.PeakPercent *= 0.7
		else:
			self.PeakPercent *= 0.7
			self.bWaterworld = True
		# Wrap Options
		self.bWrapX = True
		self.bWrapY = False
		selectionID = MAP.getCustomMapOption(3)
		if not selectionID:
			wrapString = "Cylindrical"
			if self.bPangea:
				self.eastAttenuationRange	= .30
				self.westAttenuationRange	= .30
		elif selectionID == 1:
			wrapString = "Toroidal"
			self.bWrapY = True
			if self.bPangea:
				self.northAttenuationRange	= .20
				self.southAttenuationRange	= .20
				self.eastAttenuationRange	= .30
				self.westAttenuationRange	= .30
			else:
				self.bAttenuate = False
		elif selectionID == 2:
			wrapString = "Flat"
			self.bWrapX = False

		# New World Rules
		selectionID = MAP.getCustomMapOption(4)
		if not selectionID or self.bDryland or self.bPangea:
			self.bNewWorld = False
		else:
			self.bNewWorld = True
		# Rivers
		selectionID = MAP.getCustomMapOption(5)
		if not selectionID:
			self.fRiverThreshold *= 5
		elif selectionID == 1:
			self.fRiverThreshold *= 4
		elif selectionID == 2:
			self.fRiverThreshold *= 3
		elif selectionID == 3:
			self.fRiverThreshold *= 2
		elif selectionID == 5:
			self.fRiverThreshold /= 2
		elif selectionID == 6:
			self.fRiverThreshold /= 3
		elif selectionID == 7:
			self.fRiverThreshold /= 4
		elif selectionID == 8:
			self.fRiverThreshold /= 5
		# Bonuses
		selectionID = MAP.getCustomMapOption(6)
		if not selectionID:
			self.fBonusMult = 0.0
		elif selectionID == 1:
			self.fBonusMult *= 0.50
		elif selectionID == 2:
			self.fBonusMult *= 0.75
		elif selectionID == 4:
			self.fBonusMult *= 1.25
		elif selectionID == 5:
			self.fBonusMult *= 1.50
		elif selectionID == 6:
			self.fBonusMult *= 1.75
		# Pangea Breaker
		selectionID = MAP.getCustomMapOption(7)
		if selectionID or self.bDryland or self.bPangea:
			self.bPangeaBreaker = False
		else:
			self.bPangeaBreaker = True
		# Set Option Strings
		self.optionsString = "Map Options: \n"
		if self.bPangea:
			self.optionsString += "bPangea = True\n"
		else:
			self.optionsString += "bPangea = False\n"
		self.optionsString += "World Wrap = " + wrapString + "\n"
		if self.bNewWorld:
			self.optionsString += "Allow New World = True\n"
		else:
			self.optionsString += "Allow New World = False\n"


	def AdaptToGameOptions(self):
		GC = CyGlobalContext()
		MAP = GC.getMap()
		# World Size
		self.iWidth		= MAP.getGridWidth()
		self.iHeight	= MAP.getGridHeight()
		self.iArea		= self.iWidth * self.iHeight
		self.iWorldSize	= iWorldSize = MAP.getWorldSize()
		self.iMaxLakeSize = int(round((GC.getWorldInfo(iWorldSize).getOceanMinAreaSize() - 1) * self.fMaxLakeSizeMod))
		# Too many meteors will simply destroy the Earth, it also prevent an endless loop if the pangea can't be broken.
		self.iMaxMeteorCount = 15 + 5 * iWorldSize
		# Minimum size for a meteor strike that attemps to break pangaeas.
		self.iMinMeteorSize = int(round((1.3 + iWorldSize / 1.3) / (self.bArchipelago * .5 + 1)))
		self.iMaxMeteorSize = int(round((3 + iWorldSize) / (self.bArchipelago * .5 + 1)))
		# Climate
		iClimate = MAP.getClimate()
		if iClimate == 1: # Tropical, less ice, less desert, more jungle.
			self.IceTemp		*= 0.75
			self.PermaFrostTemp *= 0.75
			self.TundraTemp		*= 0.75
			self.TaigaTemp		*= 0.75
			self.JungleTemp		*= 0.75
			self.ForestTemp		*= 0.75

			self.IceChanceMultiplier = 0.5

			self.SaltFlatsPercent	*= 0.7
			self.DunesPercent		*= 0.7
			self.DesertPercent		*= 0.7
			self.ScrubPercent		*= 0.7
			self.PlainsPercent		*= 0.8
			self.GrasslandPercent	*= 0.9
			self.LushPercent		*= 0.9
			self.MuddyPercent		*= 0.9

			self.fTemperateLat	= 0.6
			self.fPolarLat		= 0.90
			self.fTropicLat		= 0.25

			self.upLiftExponent  = 5

		elif iClimate == 2: # Arid, more desert, less wet plots.
			self.SaltFlatsPercent	= 0.10
			self.DunesPercent		= 0.20
			self.DesertPercent		= 0.35
			self.ScrubPercent		= 0.50
			self.PlainsPercent		= 0.8
			self.GrasslandPercent	= 0.9
			self.LushPercent		= 0.95
			self.MuddyPercent		= 0.98

			self.minimumRainCost = 0.01
			self.upLiftExponent  = 3
			self.fPolarRainBoost  = 0.1

		elif iClimate == 3: # Rocky, more peaks, hills and rocky terrain
			self.HillPercent	*= 1.25
			self.fRockyPercent 	*= 1.25

		elif iClimate == 4: # Cold, larger polar area, more cold territory
			self.IceTemp		*= 1.25
			self.PermaFrostTemp *= 1.25
			self.TundraTemp		*= 1.25
			self.TaigaTemp		*= 1.25
			self.JungleTemp		*= 1.25
			self.ForestTemp		*= 1.25

			self.IceChanceMultiplier = 0.9

			self.fTemperateLat	= 0.4
			self.fPolarLat		= 0.70
			self.fTropicLat		= 0.10

			self.upLiftExponent = 2
		# fMaxStartLat limits the starting location to a maximum latitude.
		self.fMaxStartLat = 90 * self.fPolarLat - self.fPolarLat**3 / 0.0569
		# Sea Level
		seaLevel = GC.getSeaLevelInfo(MAP.getSeaLevel()).getSeaLevelChange()
		if self.bEarthlike:
			if not seaLevel:
				self.fLandPercent = .35
			elif seaLevel > 0:
				self.fLandPercent = .30
			else:
				self.fLandPercent = .40
		elif self.bArchipelago:
			if not seaLevel:
				self.fLandPercent = .30
			elif seaLevel > 0:
				self.fLandPercent = .25
			else:
				self.fLandPercent = .35
		elif self.bWaterworld:
			if not seaLevel:
				self.fLandPercent = .20
			elif seaLevel > 0:
				self.fLandPercent = .10
			else:
				self.fLandPercent = .25
		elif self.bDryland:
			if not seaLevel:
				self.fLandPercent = .90
			elif seaLevel > 0:
				self.fLandPercent = .75
			else:
				self.fLandPercent = 1.0
		elif self.bPangea:
			if not seaLevel:
				self.fLandPercent = .50
			elif seaLevel > 0:
				self.fLandPercent = .40
			else:
				self.fLandPercent = .55
		# Increase land percent by lake tiles added such that # of land tiles are not impacted by large lake percentage (ocean may be though)
		self.fLandPercent = min(1.0, self.fLandPercent * (1.0 + self.fLakesPercent))
		print "Land percent = %f" % self.fLandPercent

mc = None


##############################################################################
## AreaMap
##############################################################################

class AreaMap:

	def __init__(self):
		self.iWidth	 = mc.iWidth
		self.iHeight = mc.iHeight
		self.iArea	 = mc.iArea
		self.areaID	 = array('H')


	def defineAreas(self, matchFunction):
		self.areaList = []
		self.areaID = [0] * self.iArea
		ID = 0
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				if not self.areaID[i]: # If not assigned an area yet.
					ID += 1
					areaSize, avgX, avgY, bWater = self.fillArea(x, y, ID, matchFunction)
					area = Area(ID, areaSize, avgX, avgY, bWater)
					self.areaList.append(area)


	def getAreaByID(self, ID):
		for i in xrange(len(self.areaList)):
			if self.areaList[i].ID == ID:
				return self.areaList[i]
		return None


	def getAreaByPlotIndex(self, plotIndex):
		# print "	plotIndex: %i" % plotIndex
		# print "	areaID size: %i" % (len(self.areaID))
		# print "	areaID: %i" % self.areaID[plotIndex]
		# print "	areaList size: %i" (len(self.areaList)
		# print self.areaID
		# print self.areaList
		return self.areaList[self.areaID[plotIndex] - 1]


	def getAreaMapByID(self, targetID):
		matchingArea = [0] * self.iArea
		for index, ID in enumerate(self.areaID):
			if targetID == ID:
				matchingArea[index] = 1
		return matchingArea


	def fillArea(self, x, y, ID, matchFunction):
		# We check all 8 neigbors for land, but only 4 for water.
		# This is because the game connects land squares diagonally across water,
		# but water squares are not passable diagonally across land.
		self.segStack = []
		self.size   = 0
		self.totalX = 0
		self.totalY = 0
		bWater = matchFunction(x, y)
		seg = LineSegment(y, x, x, 1)
		self.segStack.append(seg)
		seg = LineSegment(y + 1, x, x, -1)
		self.segStack.append(seg)
		while len(self.segStack) > 0:
			seg = self.segStack.pop()
			self.scanAndFillLine(seg, ID, bWater, matchFunction)
		# Set landmass position values
		avgX = float(self.totalX) / float(self.size)
		avgY = float(self.totalY) / float(self.size)
		if avgX < 0:
			avgX += self.iWidth
		elif avgX >= self.iWidth:
			avgX -= self.iWidth
		if avgY < 0:
			avgY += self.iHeight
		elif avgY >= self.iHeight:
			avgY -= self.iHeight
		return self.size, avgX, avgY, bWater


	def scanAndFillLine(self, seg, ID, bWater, matchFunction):
		# Check for y + dy being off map.
		if seg.y + seg.dy >= self.iHeight:
			if not mc.bWrapY:
				return
		# For land tiles we must look one past the x extents to include 8-connected neighbors.
		if bWater:
			landOffset = 0
		else:
			landOffset = 1
		lineFound = False
		# First scan and fill any left overhang.
		if mc.bWrapX:
			xStop1 = 0 - (self.iWidth * 20)
			xStop2 = self.iWidth * 20
		else:
			xStop1 = -1
			xStop2 = self.iWidth
		for xLeftExtreme in xrange(seg.xLeft - landOffset, xStop1, -1):
			i = GetIndex(xLeftExtreme, seg.y + seg.dy)
			if self.areaID[i] == 0 and bWater == matchFunction(xLeftExtreme, seg.y + seg.dy):
				self.areaID[i] = ID
				self.size += 1
				# Set landmass position values.
				self.totalX += xLeftExtreme
				self.totalY += seg.y + seg.dy
				lineFound = True
			else:
				# If no line was found, then xLeftExtreme is fine, but if a line was found going left,
				# then we need to increment xLeftExtreme to represent the inclusive end of the line.
				if lineFound:
					xLeftExtreme += 1
				break
		# Now scan right to find extreme right, place each found segment on stack.
		xRightExtreme = seg.xLeft # Needed sometimes? one time it was not initialized before use.
		for xRightExtreme in xrange(seg.xLeft + lineFound - landOffset, xStop2):
			i = GetIndex(xRightExtreme, seg.y + seg.dy)
			if not self.areaID[i] and bWater == matchFunction(xRightExtreme, seg.y + seg.dy):
				self.areaID[i] = ID
				self.size   += 1
				#LM - set landmass position values
				self.totalX += xRightExtreme
				self.totalY += seg.y + seg.dy
				if not lineFound:
					lineFound = True
					xLeftExtreme = xRightExtreme # Starting new line.
			elif lineFound: # Found the right end of a line segment!
				lineFound = False
				# Put same direction on stack.
				newSeg = LineSegment(seg.y + seg.dy, xLeftExtreme, xRightExtreme - 1, seg.dy)
				self.segStack.append(newSeg)
				# Determine if we must put reverse direction on stack.
				if xLeftExtreme < seg.xLeft or xRightExtreme >= seg.xRight:
					# Out of shadow so put reverse direction on stack also.
					newSeg = LineSegment(seg.y + seg.dy, xLeftExtreme, xRightExtreme - 1, -seg.dy)
					self.segStack.append(newSeg)
				if xRightExtreme >= seg.xRight + landOffset:
					break # Past the end of the parent line and this line ends.
			elif not lineFound and xRightExtreme >= seg.xRight + landOffset:
				break # Ppast the end of the parent line and no line found.
			else:
				continue #keep looking for more line segments
		if lineFound: #still a line needing to be put on stack
			lineFound = False
			#put same direction on stack
			newSeg = LineSegment(seg.y + seg.dy, xLeftExtreme, xRightExtreme - 1, seg.dy)
			self.segStack.append(newSeg)
			#determine if we must put reverse direction on stack
			if xLeftExtreme < seg.xLeft or xRightExtreme - 1 > seg.xRight:
				#out of shadow so put reverse direction on stack also
				newSeg = LineSegment(seg.y + seg.dy, xLeftExtreme, xRightExtreme - 1, -seg.dy)
				self.segStack.append(newSeg)


class LineSegment:
	def __init__(self, y, xLeft, xRight, dy):
		self.y  = y
		self.dy = dy
		self.xLeft  = xLeft
		self.xRight = xRight


class Area:
	def __init__(self, ID, size, avgX, avgY, water):
		self.ID			= ID
		self.size		= size
		self.avgX		= avgX
		self.avgY		= avgY
		self.distance	= 0.0
		self.water		= water


##############################################################################
## FloatMap
##
## This is for storing 2D map data. The 'data' field is a zero based, one
## dimensional array. To access map data by x and y coordinates, use the
## GetIndex method to obtain the 1D index, which will handle any needs for
## wrapping in the x and y directions.
##############################################################################

class FloatMap:
	def __init__(self):
		return

	def Initialize(self):
		self.iWidth  = mc.iWidth
		self.iHeight = mc.iHeight
		self.iArea	 = mc.iArea
		self.data = array('d', [0.0] * self.iArea)


	def Normalize(self):
		iLength = len(self.data)
		maxAlt = max(self.data)
		minAlt = min(self.data)
		# Subtract minAlt from all values so that all values are zero and above.
		for i in xrange(iLength):
			self.data[i] = self.data[i] - minAlt
		# Subract minAlt also from maxAlt.
		maxAlt = maxAlt - minAlt
		# Determine and apply scalar to whole map.
		if maxAlt not in (1.0, 0.0):
			scalar = 1.0 / maxAlt
			for i in xrange(iLength):
				self.data[i] = self.data[i] * scalar


	def GetZone(self, y):
		if y < 0 or y >= self.iHeight:
			return mc.NOZONE
		lat = y * 2.0 / (self.iHeight - 1.0) - 1.0
		if lat >= mc.fPolarLat:
			return mc.NPOLAR
		elif lat >= mc.fTemperateLat:
			return mc.NTEMPERATE
		elif lat >= 0.0:
			return mc.NEQUATOR
		elif lat >= -mc.fTemperateLat:
			return mc.SEQUATOR
		elif lat >= -mc.fPolarLat:
			return mc.STEMPERATE
		else:
			return mc.SPOLAR


	def GetYFromZone(self, zone, bTop):
		if bTop:
			y = self.iHeight - 1
			while y >= 0:
				if zone == self.GetZone(y):
					return y
				y -= 1
		else:
			for y in xrange(self.iHeight):
				if zone == self.GetZone(y):
					return y
		return -1


	def GetGeostrophicWindDirections(self, zone):
		if zone == mc.NPOLAR:
			return mc.SW, mc.W
		elif zone == mc.NTEMPERATE:
			return mc.NE, mc.E
		elif zone == mc.NEQUATOR:
			return mc.SW, mc.W
		elif zone == mc.SEQUATOR:
			return mc.NW, mc.W
		elif zone == mc.STEMPERATE:
			return mc.SE, mc.E
		else:
			return mc.NW, mc.W
		return -1, -1


	def GetGeostrophicPressure(self, lat):
		if lat > mc.fPolarLat:
			latRange   = 1.0 - mc.fPolarLat
			latPercent = (lat - mc.fPolarLat) / latRange
			pressure   = 1.0 - latPercent
		elif lat >= mc.fTemperateLat:
			latRange   = mc.fPolarLat - mc.fTemperateLat
			latPercent = (lat - mc.fTemperateLat) / latRange
			pressure   = latPercent
		elif lat >= 0.0:
			latPercent = lat / mc.fTemperateLat
			pressure   = 1.0 - latPercent
		elif lat > -mc.fTemperateLat:
			latPercent = lat + mc.fTemperateLat / mc.fTemperateLat
			pressure   = latPercent
		elif lat >= -mc.fPolarLat:
			latRange   = -mc.fTemperateLat + mc.fPolarLat
			latPercent = (lat + mc.fPolarLat) / latRange
			pressure   = 1.0 - latPercent
		else:
			latRange   = -mc.fPolarLat + 1.0
			latPercent = (lat + 1.0) / latRange
			pressure   = latPercent
		return pressure


	def Smooth(self, radius):
		data = self.data
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				list = pb.getCirclePoints(x, y, radius)
				avg = 0.0
				for hex in list:
					ii = GetIndex(hex.x, hex.y)
					avg += data[ii]
				data[i] = avg / len(list)


##############################################################################
## Noise Generator Class
##############################################################################
class SimplexNoise4D:
	"""The gradients are the midpoints of the vertices of a cube."""
	_Grad4D = [
		[0,1,1,1],  [0,1,1,-1],  [0,1,-1,1],  [0,1,-1,-1],
		[0,-1,1,1], [0,-1,1,-1], [0,-1,-1,1], [0,-1,-1,-1],
		[1,0,1,1],  [1,0,1,-1],  [1,0,-1,1],  [1,0,-1,-1],
		[-1,0,1,1], [-1,0,1,-1], [-1,0,-1,1], [-1,0,-1,-1],
		[1,1,0,1],  [1,1,0,-1],  [1,-1,0,1],  [1,-1,0,-1],
		[-1,1,0,1], [-1,1,0,-1], [-1,-1,0,1], [-1,-1,0,-1],
		[1,1,1,0],  [1,1,-1,0],  [1,-1,1,0],  [1,-1,-1,0],
		[-1,1,1,0], [-1,1,-1,0], [-1,-1,1,0], [-1,-1,-1,0]
	]
	"""A lookup table to traverse the simplex around a given point in 4D."""
	_Simplex = [
		[0,1,2,3],[0,1,3,2],[0,0,0,0],[0,2,3,1],[0,0,0,0],[0,0,0,0],[0,0,0,0],[1,2,3,0],
		[0,2,1,3],[0,0,0,0],[0,3,1,2],[0,3,2,1],[0,0,0,0],[0,0,0,0],[0,0,0,0],[1,3,2,0],
		[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],
		[1,2,0,3],[0,0,0,0],[1,3,0,2],[0,0,0,0],[0,0,0,0],[0,0,0,0],[2,3,0,1],[2,3,1,0],
		[1,0,2,3],[1,0,3,2],[0,0,0,0],[0,0,0,0],[0,0,0,0],[2,0,3,1],[0,0,0,0],[2,1,3,0],
		[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],
		[2,0,1,3],[0,0,0,0],[0,0,0,0],[0,0,0,0],[3,0,1,2],[3,0,2,1],[0,0,0,0],[3,1,2,0],
		[2,1,0,3],[0,0,0,0],[0,0,0,0],[0,0,0,0],[3,1,0,2],[0,0,0,0],[3,2,0,1],[3,2,1,0]
	]
	# The skewing and unskewing factors are hairy again for the 4D case
	_G4 = (5.0 - sqrt(5.0)) / 20.0
	_F4 = (sqrt(5.0) - 1.0) / 4.0

	def __init__(self, iPeriod = 512):
		# Create permutation tables.
		self.randomize(iPeriod)

	def randomize(self, iPeriod = 512):
		"""Randomize the permutation table used by the noise functions.
		The same value is always returned for a given coordinate unless the	permutation table changes."""
		self.period = iPeriod
		permTable = range(self.period)
		shuffle(permTable)
		# Double permutation array so we don't need to wrap
		self.perm = permTable * 2

	def fBm(self, x, y, z, w, octaves, scale, lacunarity, persistence0, persistence1, fExp=1, min=0, max=1):
		# fBm - fractal Brownian motion
		frequency = scale
		amplitude = 1.0
		maxAmplit = .0
		noise = .0
		#add successively smaller, higher-frequency terms
		for i in xrange(octaves):
			noise += (self.getNoise(x * frequency, y * frequency, z * frequency, w * frequency)/2 + .5) * amplitude
			maxAmplit += amplitude
			if not i:
				amplitude *= persistence0
			else: amplitude *= persistence1

			if amplitude < .1:
				break
			frequency *= lacunarity
		# Normalize within 0-1 and apply exponent
		noise = (noise / maxAmplit)**fExp
		# Return scaled to min-max range.
		return min + noise * (max - min)

	def getNoise(self, x, y, z, w):
		"""4D Raw Simplex noise.
		Return a floating point value from -1 to 1 for the given x,y,z,w coordinate."""
		# Skew the (x,y,z,w) space to determine which cell of 24 simplices we're in.
		F4 = self._F4
		G4 = self._G4
		s = (x + y + z + w) * F4
		i = int(x + s)
		j = int(y + s)
		k = int(z + s)
		l = int(w + s)
		t = (i + j + k + l) * G4
		# Unskew the cell origin back to (x, y, z, w) space.
		X0 = i - t
		Y0 = j - t
		Z0 = k - t
		W0 = l - t
		# The x, y, z & w distances from the cell origin.
		x0 = x - X0
		y0 = y - Y0
		z0 = z - Z0
		w0 = w - W0
		# For the 4D case, the simplex is a 4D shape I won't even try to describe.
		# To find out which of the 24 possible simplices we're in, we need to
		# determine the magnitude ordering of x0, y0, z0 and w0.
		# The method below is a good way of finding the ordering of x, y, z & w and
		# then find the correct traversal order for the simplex we're in.
		# First, six pair-wise comparisons are performed between each possible pair of the four coordinates,
		# and the results are used to add up binary bits for an integer index.
		if x0 > y0:
			c1 = 32
		else:
			c1 = 0
		if x0 > z0:
			c2 = 16
		else:
			c2 = 0
		if y0 > z0:
			c3 = 8
		else:
			c3 = 0
		if x0 > w0:
			c4 = 4
		else:
			c4 = 0
		if y0 > w0:
			c5 = 2
		else:
			c5 = 0
		if z0 > w0:
			c6 = 1
		else:
			c6 = 0
		c = c1 + c2 + c3 + c4 + c5 + c6

		i1, j1, k1, l1 = 0,0,0,0 # The integer offsets for the second simplex corner
		i2, j2, k2, l2 = 0,0,0,0 # The integer offsets for the third simplex corner
		i3, j3, k3, l3 = 0,0,0,0 # The integer offsets for the fourth simplex corner
		# simplex[c] is a 4-vector with the numbers 0, 1, 2 and 3 in some order.
		# Many values of c will never occur, since e.g. x>y>z>w makes x<z, y<w and x<w
		# impossible. Only the 24 indices which have non-zero entries make any sense.
		# We use a thresholding to set the coordinates in turn from the largest magnitude.
		# The number 3 in the "simplex" array is at the position of the largest coordinate.
		Simplex = self._Simplex
		if Simplex[c][0] >= 3:
			i1 = 1
		else:
			i1 = 0
		if Simplex[c][1] >= 3:
			j1 = 1
		else:
			j1 = 0
		if Simplex[c][2] >= 3:
			k1 = 1
		else:
			k1 = 0
		if Simplex[c][3] >= 3:
			l1 = 1  
		else:
			l1 = 0
		# The number 2 in the "simplex" array is at the second largest coordinate.
		if Simplex[c][0] >= 2:
			i2 = 1
		else:
			i2 = 0
		if Simplex[c][1] >= 2:
			j2 = 1
		else:
			j2 = 0
		if Simplex[c][2] >= 2:
			k2 = 1
		else:
			k2 = 0
		if Simplex[c][3] >= 2:
			l2 = 1
		else:
			l2 = 0
		# The number 1 in the "simplex" array is at the second smallest coordinate.
		if Simplex[c][0] >= 1:
			i3 = 1
		else:
			i3 = 0
		if Simplex[c][1] >= 1:
			j3 = 1
		else:
			j3 = 0
		if Simplex[c][2] >= 1:
			k3 = 1
		else:
			k3 = 0
		if Simplex[c][3] >= 1:
			l3 = 1
		else:
			l3 = 0
		# The fifth corner has all coordinate offsets = 1, so no need to look that up.
		x1 = x0 - i1 + G4 # Offsets for second corner in (x,y,z,w) coords
		y1 = y0 - j1 + G4
		z1 = z0 - k1 + G4
		w1 = w0 - l1 + G4
		x2 = x0 - i2 + 2.0 * G4 # Offsets for third corner in (x,y,z,w) coords
		y2 = y0 - j2 + 2.0 * G4
		z2 = z0 - k2 + 2.0 * G4
		w2 = w0 - l2 + 2.0 * G4
		x3 = x0 - i3 + 3.0 * G4 # Offsets for fourth corner in (x,y,z,w) coords
		y3 = y0 - j3 + 3.0 * G4
		z3 = z0 - k3 + 3.0 * G4
		w3 = w0 - l3 + 3.0 * G4
		x4 = x0 - 1.0 + 4.0 * G4 # Offsets for last corner in (x,y,z,w) coords
		y4 = y0 - 1.0 + 4.0 * G4
		z4 = z0 - 1.0 + 4.0 * G4
		w4 = w0 - 1.0 + 4.0 * G4

		# Work out the hashed gradient indices of the five simplex corners
		period = self.period
		ii = i % period
		jj = j % period
		kk = k % period
		ll = l % period
		pe = self.perm
		gi0 = pe[ii + pe[jj + pe[kk + pe[ll]]]] % 32
		gi1 = pe[ii + i1 + pe[jj + j1 + pe[kk + k1 + pe[ll + l1]]]] % 32
		gi2 = pe[ii + i2 + pe[jj + j2 + pe[kk + k2 + pe[ll + l2]]]] % 32
		gi3 = pe[ii + i3 + pe[jj + j3 + pe[kk + k3 + pe[ll + l3]]]] % 32
		gi4 = pe[ii + 1 + pe[jj + 1 + pe[kk + 1 + pe[ll + 1]]]] % 32

		# Noise contributions from the five corners.
		n0,n1,n2,n3,n4 = 0.0,0.0,0.0,0.0,0.0
		# Calculate the contribution from the five corners
		gr = self._Grad4D
		t0 = 0.6 - x0*x0 - y0*y0 - z0*z0 - w0*w0
		if t0 < 0:
			n0 = 0.0
		else:
			t0 *= t0
			n0 = t0 * t0 * self.dot4D(gr[gi0], x0, y0, z0, w0)

		t1 = 0.6 - x1*x1 - y1*y1 - z1*z1 - w1*w1
		if t1 < 0:
			n1 = 0.0
		else:
			t1 *= t1
			n1 = t1 * t1 * self.dot4D(gr[gi1], x1, y1, z1, w1)

		t2 = 0.6 - x2*x2 - y2*y2 - z2*z2 - w2*w2
		if t2 < 0:
			n2 = 0.0
		else:
			t2 *= t2
			n2 = t2 * t2 * self.dot4D(gr[gi2], x2, y2, z2, w2)

		t3 = 0.6 - x3*x3 - y3*y3 - z3*z3 - w3*w3
		if t3 < 0:
			n3 = 0.0
		else:
			t3 *= t3
			n3 = t3 * t3 * self.dot4D(gr[gi3], x3, y3, z3, w3)

		t4 = 0.6 - x4*x4 - y4*y4 - z4*z4 - w4*w4
		if t4 < 0:
			n4 = 0.0
		else:
			t4 *= t4
			n4 = t4 * t4 * self.dot4D(gr[gi4], x4, y4, z4, w4)

		# Sum up and scale the result to cover the range [-1,1]
		return 27.0 * (n0 + n1 + n2 + n3 + n4)

	def dot4D(self, g, x, y, z, w):
		return g[0]*x + g[1]*y + g[2]*z + g[3]*w


##############################################################################
## Landmass Generator Class
##############################################################################
class ElevationMap(FloatMap):
	def __init__(self):
		self.iWidth  = mc.iWidth
		self.iHeight = mc.iHeight
		self.iArea	 = mc.iArea
		self.data	 = array('d', [0.0] * self.iArea)


	def GenerateElevationMap(self):
		timer = BugUtil.Timer('Generating Elevation Map')
		iWidthLoc  = self.iWidth
		iHeightLoc = self.iHeight
		iAreaLoc   = self.iArea
		bWrapY = mc.bWrapY
		bWrapX = mc.bWrapX
		bAttenuate = mc.bAttenuate
		fLandPercent = mc.fLandPercent
		iSampling0 = mc.iWorldSize + 1
		iSampling1 = iSampling0
		fBaseFreq = mc.fBaseFreq
		fBaseFreq1 = fBaseFreq*6
		fLacunarity = mc.fLacunarity
		# Roughness oscillation.
		fPersFreq = fBaseFreq*6
		fMinPersi = mc.fMinPersi
		fMaxPersi = mc.fMaxPersi
		# Noise Maps
		fPersiNoise = SimplexNoise4D()
		heightNoise = SimplexNoise4D()
		detailNoise = SimplexNoise4D()
		i = -1
		for y in xrange(iHeightLoc):
			yP = 1.0 * y/iHeightLoc
			c2 = cos(yP * 2*pi) + 2
			c4 = sin(yP * 2*pi) + 4
			for x in xrange(iWidthLoc):
				i += 1
				xP = 1.0 * x/iWidthLoc
				c1 = cos(xP * 2*pi)*1.1 + 4
				c3 = sin(xP * 2*pi)*1.1 + 2
				fPersistence = fPersiNoise.fBm(c1, c2, c3, c4, 6, fPersFreq, 1.2, .6, .5, 2.6, fMinPersi, fMaxPersi)
				self.data[i] = heightNoise.fBm(c1, c2, c3, c4, 12, fBaseFreq, fLacunarity, fMinPersi, fPersistence)
				if self.data[i] > 0.75:
					self.data[i] -= detailNoise.fBm(c1, c2, c3, c4, 6, fBaseFreq1, 1.4, .5, .6, 3, .0, .2)
				elif self.data[i] > 0.5:
					self.data[i] += detailNoise.fBm(c1, c2, c3, c4, 6, fBaseFreq1, 1.4, .5, .6, 3, .0, .2)
				elif self.data[i] > 0.25:
					self.data[i] -= detailNoise.fBm(c1, c2, c3, c4, 6, fBaseFreq1, 1.4, .5, .6, 3, .0, .2)
				else:
					self.data[i] += detailNoise.fBm(c1, c2, c3, c4, 6, fBaseFreq1, 1.4, .5, .6, 3, .0, .2)
		self.Normalize()
		if bAttenuate:
			print "	Attenuating"
			fMinY = 0.05 * iHeightLoc
			fMaxY = 0.95 * iHeightLoc
			fSouthRange	 = mc.southAttenuationRange
			fNorthRange	 = mc.northAttenuationRange
			fEastRange	 = mc.eastAttenuationRange
			fWestRange	 = mc.westAttenuationRange
			if not fNorthRange:
				northY = -1
			else:
				northY = iHeightLoc * fNorthRange
				northAtFac = mc.northAttenuationFactor
				northStep = (1-northAtFac) / northY

			if not fSouthRange:
				southY = -1
			else:
				southY = (iHeightLoc - 1) - iHeightLoc * fSouthRange
				southAtFac = mc.southAttenuationFactor
				southStep = (1-southAtFac) / (iHeightLoc * fSouthRange)

			if not fWestRange:
				fWestX = -1
			else:
				fWestX  = iWidthLoc * fWestRange
				fWestAtFac = mc.westAttenuationFactor
				fWestStep = (1-fWestAtFac) / fWestX

			if not fEastRange:
				fEastX = -1
			else:
				fEastX  = (iWidthLoc - 1) - iWidthLoc * fEastRange
				fEastAtFac = mc.eastAttenuationFactor
				fEastStep = (1-fEastAtFac) / (iWidthLoc * fEastRange)
			i = -1
			for y in xrange(iHeightLoc):
				for x in xrange(iWidthLoc):
					i += 1
					yAttenuation = 1.0
					if y < northY:
						yAttenuation = northAtFac + northStep * y
					elif y > southY and southY != -1:
						yAttenuation = southAtFac + southStep * (iHeightLoc - 1 - y)

					xAttenuation = 1.0
					if x < fWestX:
						xAttenuation = fWestAtFac + fWestStep * x
					elif x > fEastX and fEastX != -1:
						xAttenuation = fEastAtFac + fEastStep * (iWidthLoc - 1 - x)
					self.data[i] *= yAttenuation * xAttenuation

		self.fLandHeight = FindThresholdFromPercent(self.data, fLandPercent)
		timer.log()
		# Handle Pangea and fill in random lakes.
		print "\n", "Elevation Map - Post Process"
		timer = BugUtil.Timer('Elevation Map - Post Process')
		if mc.bPangeaBreaker:
			pb.breakPangeas()
		self.FillInLakes(fLandPercent)
		fLandHeightLoc = self.fLandHeight
		# Prepare new lakes.
		fMinLakeAlt = self.createLakeDepressions(self.data, fLandHeightLoc, fLandPercent)
		# Create elevation relative delta map using the lowest nearest neighbor elevation.
		self.relAltMap3x3 = array('d', [0.0] * iAreaLoc)
		i = -1
		n = 0
		for y in xrange(iHeightLoc):
			for x in xrange(iWidthLoc):
				i += 1
				myAlt = self.data[i]
				# if water tile, deltamap height represents depth below sea level
				if myAlt < fLandHeightLoc:
					self.relAltMap3x3[i] = fLandHeightLoc - myAlt
					continue
				bCoastal = False
				minNeighborAlt = 1.0
				# examine neighbors to find lowest; note if coastal
				for direction in xrange(1, 9):
					xx, yy = GetNeighbor(x, y, direction)
					ii = GetIndex(xx, yy)
					if ii >= 0:
						if self.data[ii] < minNeighborAlt:
							minNeighborAlt = self.data[ii]
							if self.data[ii] < fLandHeightLoc:
								bCoastal = True
				# if tile is a pit, mark it
				if myAlt < minNeighborAlt and myAlt >= fMinLakeAlt:
					n += 1
					self.relAltMap3x3[i] = -1.0 # Lake Pit Denotation
				# otherwise, mark altitude diff (lower if coastal)
				elif bCoastal:
					self.relAltMap3x3[i] = (myAlt - minNeighborAlt) * 0.2
				else:
					self.relAltMap3x3[i] = (myAlt - minNeighborAlt)
		print "	Pits Found: %d" % n
		# Create a delta map version that excludes water tiles so hill and peak percent is relative to land.
		# Also create a list of ocean elevations for later use in defining trenches.
		bTrench = True
		landDelta = []
		aquaDelta = []
		i = -1
		for y in xrange(iHeightLoc):
			if bAttenuate:
				if y < fMinY or fMaxY <= y:
					bTrench = False
				else:
					bTrench = True
			for x in xrange(iWidthLoc):
				i += 1
				if self.data[i] >= fLandHeightLoc: # Not Below Sea Level.
					landDelta.append(self.relAltMap3x3[i])
				elif bTrench:
					aquaDelta.append(self.data[i])
		self.fHillDelta	= FindThresholdFromPercent(landDelta, mc.HillPercent + mc.PeakPercent)
		self.fPeakDelta	= FindThresholdFromPercent(landDelta, mc.PeakPercent)
		# Set up base trench data
		fTrenchesPercent = mc.fTrenchesPercent
		self.iNumTrenches = int(iAreaLoc * fTrenchesPercent * (1.0 - fLandPercent))
		fDeepWaterPercent = 1.0 - 10 * fTrenchesPercent
		if fDeepWaterPercent < .1:
			fDeepWaterPercent = .1
		elif fDeepWaterPercent > .99:
			fDeepWaterPercent = .99
		self.fTrenchEle	= FindThresholdFromPercent(aquaDelta, fDeepWaterPercent)
		timer.log()


	def IsBelowSeaLevel(self, x, y):
		i = GetIndex(x, y)
		if self.data[i] < self.fLandHeight:
			return True
		return False


	def isDeepWaterMatch(self, x, y):
		fLandHeightLoc = self.fLandHeight
		i = GetIndex(x, y)
		if self.data[i] >= fLandHeightLoc:
			return False
		for direction in xrange(1, 9):
			xx, yy = GetNeighbor(x, y, direction)
			ii = GetIndex(xx, yy)
			if ii >= 0 and self.data[ii] >= fLandHeightLoc:
				return False
		return True


	def FillInLakes(self, fLandPercent):
		am = AreaMap()
		while True:
			iCount = 0
			self.fLandHeight = fLandHeightLoc = FindThresholdFromPercent(self.data, fLandPercent)
			am.defineAreas(self.IsBelowSeaLevel)
			i = -1
			for y in xrange(self.iHeight):
				for x in xrange(self.iWidth):
					i += 1
					if self.data[i] < fLandHeightLoc: # If IsBelowSeaLevel().
						# Check the size of this body of water, if lake-size, change to land.
						for a in am.areaList:
							if a.ID == am.areaID[i] and a.size <= mc.iMaxLakeSize:
								self.data[i] = (1 - fLandHeightLoc) * 0.1 + fLandHeightLoc
								iCount += 1
			if iCount == 0:
				break


	def createLakeDepressions(self, elevationData, fLandHeight, fLandPercent):
		print "	Creating lake depressions"
		fPolarLat = mc.fPolarLat
		landList = []
		indexList = array('B', [0] * self.iArea)
		# Min altitude for lakes is fRelMinLakeAlt multiple of distance from max normalized altitude of 1.0;
		# e.g. if sea level (fLandHeight) is 0.7 and fRelMinLakeAlt 0.33, this makes 0.8 the actual min lake altitude.
		fMinLakeAlt = LinearMapping(0, 1, mc.fRelMinLakeAlt, fLandHeight, 1)

		# Generate a list of tiles that are possible to be lake pits
		iStartY = int(round(self.iHeight * (1 - fPolarLat)))
		iEndY	= int(round(self.iHeight * fPolarLat))
		i = iStartY * self.iWidth - 1 #omfg off by one errors are the worst
		for y in xrange(iStartY, iEndY):
			for x in xrange(self.iWidth):
				i += 1
				# if land tile equal or above min altitude
				if elevationData[i] >= fMinLakeAlt:
					bPit = True
					# loop thru adjacents to check for tiles to ignore
					for direction in xrange(1, 9):
						xx, yy = GetNeighbor(x, y, direction)
						ii = GetIndex(xx, yy)
						# if invalid adjacency (off map edge w/o wrapping), ignore this adjacency but keep checking other ones
						if ii == -1:
							continue
						# if adjacent also equal or below min altitude, or adjacent to already selected lake potential spot; original cannot be lake
						if elevationData[ii] <= fMinLakeAlt or indexList[ii]:
							bPit = False
							break
					# add valid to potential lake spot, if no invalid adjacencies
					if bPit:
						landList.append((x, y, i))
						indexList[i] = 1
		shuffle(landList)
		print "	Possible pits: %d" % len(landList)
		self.iNumLakePits = int(round(self.iArea * mc.fLandPercent * mc.fLakesPercent * 0.5))
		iPitsMade = 0
		# look thru tiles that match core and adjacency criteria to make a pit
		for x, y, i in landList:
			fLowestAlt = 1.0
			# find lowest neighbor
			for direction in xrange(1, 9):
				xx, yy = GetNeighbor(x, y, direction)
				ii = GetIndex(xx, yy)
				if ii >= 0:
					if elevationData[ii] < fLowestAlt:
						fLowestAlt = elevationData[ii]
			# lower tile to just below altitude of lowest neighbor if necessary. fLowestAlt > fLakeAltThresh by above landList filter
			if elevationData[i] >= fLowestAlt:
				elevationData[i] = max(fMinLakeAlt, fLowestAlt - 0.001)
			iPitsMade += 1
			if iPitsMade == self.iNumLakePits:
				break
		print "	Made %d pits from desired %d" % (iPitsMade, self.iNumLakePits)
		return fMinLakeAlt

em = None


##############################################################################
## Climate System
##############################################################################

class ClimateMap:
	def __init__(self):
		return


	def GenerateTemperatureMap(self):
		print "	Generating Temperature Map"
		self.iHeight = iHeight	= mc.iHeight
		self.iWidth  = iWidth	= mc.iWidth
		self.iArea	 = iArea	= mc.iArea
		self.aboveSeaLevelMap = aboveSeaLevelMapLoc = array('d', [0.0] * iArea)
		self.TemperatureMap	= FloatMap()
		self.TemperatureMap.Initialize()
		fLandHeight = em.fLandHeight
		self.createDistanceToOceanMap(fLandHeight)
		# Set attributes & locals
		maxWaTemp = mc.maxWaterTemp
		minWaTemp = mc.minWaterTemp
		iWorldSize = mc.iWorldSize
		fLatFactor = 4 / ((iHeight - 1.0) ** 2)
		AboveSeaRange = (1 - fLandHeight)
		fModifier = iWidth / 12.0
		disToOceanRange = iWidth + fModifier
		i = -1
		for y in xrange(iHeight):
			# Base temperature derived from latitude
			fLatitudeTemp	= fLatFactor * y * (iHeight - 1.0 - y)
			fWaterTemp		= fLatitudeTemp * maxWaTemp + minWaTemp
			for x in xrange(iWidth):
				i += 1
				if em.data[i] < fLandHeight: # If IsBelowSeaLevel().
					self.TemperatureMap.data[i] = fWaterTemp
					aboveSeaLevelMapLoc[i] = 0.0
				else:
					# Modify temperature by altitude
					aboveSeaLevelMapLoc[i] = (em.data[i] - fLandHeight) / AboveSeaRange
					fLatAltTemp = fLatitudeTemp * (1.0 - aboveSeaLevelMapLoc[i])
					# Modify temperature by distance to Ocean
					if self.toOceanDist[i] <= 1 + iWorldSize:
						fDistanceToOcean = 1.0 + (fWaterTemp - fLatAltTemp) / self.toOceanDist[i]
					else:
						fDistanceToOcean = 1 + (self.toOceanDist[i] + fModifier) / disToOceanRange
					self.TemperatureMap.data[i] = fLatAltTemp * fDistanceToOcean
		# self.TemperatureMap.Smooth( iWidth / 32 )
		self.TemperatureMap.Normalize()
		fRange = iHeight / 2.0 - 1.0
		i = -1
		for y in xrange(iHeight):
			if y < iHeight * 0.25:
				for x in xrange(iWidth):
					i += 1
					self.TemperatureMap.data[i] = 2.0 * self.TemperatureMap.data[i] * y / fRange
			elif y >= iHeight * 0.75:
				for x in xrange(iWidth):
					i += 1
					self.TemperatureMap.data[i] = 2.0 * self.TemperatureMap.data[i] * (iHeight - 1.0 - y) / fRange
			else:
				i = (y + 1) * iWidth - 1


	def GenerateRainfallMap(self):
		print "	Generating Rainfall Map"
		geoMap				= FloatMap()
		moistureMap			= FloatMap()
		initialRainfall		= FloatMap()
		geostrophicRain		= FloatMap()
		self.RainfallMap	= FloatMap()
		geoMap.Initialize()
		initialRainfall.Initialize()
		geostrophicRain.Initialize()
		self.RainfallMap.Initialize()
		iArea	= self.iArea
		iHeight = mc.iHeight
		iWidth  = mc.iWidth
		sortedTempMap = []
		i = -1
		for y in xrange(iHeight):
			lat = y * 2.0 / (iHeight - 1.0) - 1.0
			pressure = em.GetGeostrophicPressure(lat)
			for x in xrange(iWidth):
				i += 1
				geoMap.data[i] = pressure
				sortedTempMap.append((x, y, self.TemperatureMap.data[i]))
		geoMap.Normalize()
		sortedTempMap.sort(lambda a, b: cmp(a[2], b[2]))
		sortedGeoMap = [(0, 0, 0.0)] * iArea
		SW	= mc.SW
		SE	= mc.SE
		W	= mc.W
		geoIndex = 0
		for zone in xrange(6):
			topY	= em.GetYFromZone(zone, True)
			bottomY = em.GetYFromZone(zone, False)
			if not (topY == -1 and bottomY == -1):
				if topY == -1:
					topY = iHeight - 1
				if bottomY == -1:
					bottomY = 0
				dir1, dir2 = em.GetGeostrophicWindDirections(zone)
				if (dir1 == SW) or (dir1 == SE):
					yStart = topY
					yStop  = bottomY - 1
					incY   = -1
				else:
					yStart = bottomY
					yStop  = topY + 1
					incY   = 1
				if dir2 == W:
					xStart = iWidth - 1
					xStop  = -1
					incX   = -1
				else:
					xStart = 0
					xStop = iWidth
					incX = 1
				for y in xrange(yStart, yStop, incY):
					# Each line should start on water to avoid vast areas without rain.
					xxStart = xStart
					xxStop  = xStop
					for x in xrange(xStart, xStop, incX):
						if em.IsBelowSeaLevel(x, y):
							xxStart = x
							xxStop = x + iWidth * incX
							break
					for x in xrange(xxStart, xxStop, incX):
						i = GetIndex(x, y)
						if i >= 0:
							sortedGeoMap[geoIndex] = (x, y, geoMap.data[i])
							geoIndex += 1
		fLandHeight = em.fLandHeight
		# If there are no water plots lets pretend that 10% of the plots are water anyway; if not we get an empty RainMap.
		if fLandHeight <= 0.0:
			fLandHeight = FindThresholdFromPercent(em.data, 0.9)
		moistureMap.Initialize()
		for i in xrange(len(sortedTempMap)):
			x = sortedTempMap[i][0]
			y = sortedTempMap[i][1]
			self.DistributeRain(x, y, self.TemperatureMap, initialRainfall, moistureMap, False)
		moistureMap.Initialize()
		for i in xrange(len(sortedGeoMap)):
			x = sortedGeoMap[i][0]
			y = sortedGeoMap[i][1]
			self.DistributeRain(x, y, geoMap, geostrophicRain, moistureMap, True)
		# Zero below sea level for proper percent threshold finding
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if em.data[i] < fLandHeight:
					initialRainfall.data[i] = 0.0
					geostrophicRain.data[i] = 0.0
					self.RainfallMap.data[i] = 0.0
		initialRainfall.Normalize()
		geostrophicRain.Normalize()
		fGeostroFactor = mc.geostrophicFactor
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if em.data[i] >= fLandHeight:
					self.RainfallMap.data[i] = 1.0*(initialRainfall.data[i] + 2 * self.aboveSeaLevelMap[i] + geostrophicRain.data[i] * fGeostroFactor) / self.toOceanDist[i]
		self.RainfallMap.Normalize()


	def DistributeRain(self, x, y, pressureMap, RainfallMap, moistureMap, boolGeostrophic):
		i = GetIndex(x, y)
		if em.data[i] < em.fLandHeight:
			moistureMap.data[i] = self.TemperatureMap.data[i]
		elif em.relAltMap3x3[i] >= em.fPeakDelta or em.relAltMap3x3[i] == -1.0:
			moistureMap.data[i] = 1.0 - self.TemperatureMap.data[i]
		# Make list of neighbors.
		nList = []
		if boolGeostrophic:
			zone = em.GetZone(y)
			dir1, dir2 = em.GetGeostrophicWindDirections(zone)
			x1, y1 = GetNeighbor(x, y, dir1)
			ii = GetIndex(x1, y1)
			# Neighbor must be on map and in same wind zone.
			if ii >= 0 and (em.GetZone(y1) == em.GetZone(y)):
				nList.append((x1, y1))
			x2, y2 = GetNeighbor(x, y, dir2)
			ii = GetIndex(x2, y2)
			if ii >= 0:
				nList.append((x2, y2))
		else:
			for direction in xrange(1, 9):
				xx, yy = GetNeighbor(x, y, direction)
				ii = GetIndex(xx, yy)
				if ii >= 0 and pressureMap.data[i] <= pressureMap.data[ii]:
					nList.append((xx, yy))
		nListLength = len(nList)
		if nListLength == 0 or (boolGeostrophic and nListLength == 1):
			cost = moistureMap.data[i]
			RainfallMap.data[i] = cost
			return
		elif boolGeostrophic:
			geoLatWindStr = mc.geostrophicLateralWindStrength
		moisturePerNeighbor = 1.0*moistureMap.data[i] / nListLength
		# Drop rain and pass moisture to neighbors
		cost	  = mc.minimumRainCost
		upLiftExp = mc.upLiftExponent
		value1 = pressureMap.data[i] ** upLiftExp
		value2 = 1.0 - self.TemperatureMap.data[i]
		if value1 > value2:
			upLiftSource = value1
		else:
			upLiftSource = value2
		for n in xrange(nListLength):
			xx = nList[n][0]
			yy = nList[n][1]
			ii = GetIndex(xx, yy)
			value1 = pressureMap.data[ii] ** upLiftExp
			value2 = 1.0 - self.TemperatureMap.data[ii]
			if value1 > value2:
				upLiftDest = value1
			else:
				upLiftDest = value2
			value = cost + upLiftDest - upLiftSource 
			if cost < value:
				cost = value
			if boolGeostrophic:
				if n == 1:
					moisturePerNeighbor = (1.0 - geoLatWindStr) * moistureMap.data[i]
				else:
					moisturePerNeighbor = geoLatWindStr * moistureMap.data[i]
			RainfallMap.data[i] = RainfallMap.data[i] + cost * moisturePerNeighbor
			# Pass moisture to neighbor.
			moistureMap.data[ii] = moistureMap.data[ii] + moisturePerNeighbor - (cost * moisturePerNeighbor)


	def createDistanceToOceanMap(self, fLandHeight):
		self.toOceanDist = array('H')
		processQueue = []
		if mc.bDryland:
			self.toOceanDist = [1] * self.iArea
			return
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				if em.data[i] >= fLandHeight:
					self.toOceanDist.append(1000)
				else:
					self.toOceanDist.append(0)
					processQueue.append((x, y, i))
		while len(processQueue) > 0:
			x, y, i = processQueue[0]
			del processQueue[0]
			distanceToOcean = self.toOceanDist[i]
			for direction in xrange(1, 9):
				xx, yy = GetNeighbor(x, y, direction)
				ii = GetIndex(xx, yy)
				if ii >= 0:
					neighborDistanceToLand = self.toOceanDist[ii]
					if neighborDistanceToLand > distanceToOcean + 1:
						self.toOceanDist[ii] = distanceToOcean + 1
						processQueue.append((xx, yy, ii))

cm = None


class TerrainMap:
	def __init__(self):
		self.iArea = iArea = mc.iArea
		self.plotData = [0] * iArea
		self.terrData = [0] * iArea


	def GeneratePlotMap(self):
		self.iWidth  = iWidth  = mc.iWidth
		self.iHeight = iHeight = mc.iHeight
		LAND	= mc.LAND
		HILL	= mc.HILL
		PEAK	= mc.PEAK
		fLandHeight	= em.fLandHeight
		fHillDelta	= em.fHillDelta
		fPeakDelta	= em.fPeakDelta
		elevation	= em.data
		relAlt		= em.relAltMap3x3
		plotData	= self.plotData
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if elevation[i] < fLandHeight: # If IsBelowSeaLevel().
					continue
				elif relAlt[i]	< fHillDelta:
					plotData[i] = LAND
				elif relAlt[i]	< fPeakDelta:
					plotData[i] = HILL
				else:
					plotData[i] = PEAK
		# Break up large clusters of hills and peaks
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				hillList = []
				peakList = []
				if plotData[i] == HILL:
					hillList.append(i)
					for yy in xrange(y, y + 3):
						for xx in xrange(x + 1, x + 3):
							ii = GetIndex(xx, yy)
							if ii >= 0 and plotData[ii] == HILL:
								hillList.append(ii)
					if len(hillList) > 6:
						shuffle(hillList)
						plotData[hillList.pop()] = PEAK
						plotData[hillList.pop()] = LAND
				elif plotData[i] == PEAK:
					peakList.append(i)
					for yy in xrange(y, y + 3):
						for xx in xrange(x + 1, x + 3):
							ii = GetIndex(xx, yy)
							if ii >= 0 and plotData[ii] == PEAK:
								peakList.append(ii)
					if len(peakList) > 5:
						shuffle(peakList)
						plotData[peakList.pop()] = HILL
						plotData[peakList.pop()] = HILL


	def GenerateTerrainMap(self):
		# Get minimum rainfall on land
		Rainfall = cm.RainfallMap.data
		minRain = 10.0
		for i in xrange(self.iArea):
			if self.plotData[i]:
				if Rainfall[i] < minRain:
					minRain = Rainfall[i]
		# Normalize terrain rainfall thresholds
		self.desertThreshold	= desertThreshoLoc = FindValueFromPercent(Rainfall, mc.DesertPercent)
		self.saltflatsThreshold = saltFlatThresLoc = FindValueFromPercent(Rainfall, mc.SaltFlatsPercent)
		self.scrubThreshold		= scrubThresholLoc = FindValueFromPercent(Rainfall, mc.ScrubPercent)
		self.plainsThreshold	= plainThresholLoc = FindValueFromPercent(Rainfall, mc.PlainsPercent)
		self.lushThreshold		= lushThresholdLoc = FindValueFromPercent(Rainfall, mc.LushPercent)

		dunesThresholLoc = FindValueFromPercent(Rainfall, mc.DunesPercent)
		grassThresholLoc = FindValueFromPercent(Rainfall, mc.GrasslandPercent)
		muddyThresholLoc = FindValueFromPercent(Rainfall, mc.MuddyPercent)
		#################################################
		## Terrain Picker
		#################################################
		HILL	= mc.HILL
		ICE		= mc.ICE
		FROST	= mc.FROST
		TUNDRA	= mc.TUNDRA
		TAIGA	= mc.TAIGA
		GRASS	= mc.GRASS
		LUSH	= mc.LUSH
		MUDDY	= mc.MUDDY
		MARSH	= mc.MARSH
		PLAINS	= mc.PLAINS
		ROCKY		= mc.ROCKY
		ROCKY_ARID	= mc.ROCKY_ARID
		ROCKY_COLD	= mc.ROCKY_COLD
		BARREN	= mc.BARREN
		SCRUB	= mc.SCRUB
		DESERT	= mc.DESERT
		DUNES	= mc.DUNES
		SALT_FLATS = mc.SALT_FLATS
		fRockyPercent = mc.fRockyPercent
		fIceTemp	= mc.IceTemp
		fFrostTemp	= mc.PermaFrostTemp
		fTundraTemp	= mc.TundraTemp
		fTaigaTemp	= mc.TaigaTemp
		fScrubTemp	= mc.fScrubTemp
		Temperature = cm.TemperatureMap.data
		terrData	= self.terrData
		plotData	= self.plotData
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				if not plotData[i]:
					continue
				RainData = Rainfall[i]
				tempData = Temperature[i]
				if tempData < fIceTemp:
					terrData[i] = ICE
				elif tempData < fFrostTemp:
					terrData[i] = FROST
				elif tempData < fTundraTemp:
					if plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY_COLD
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY_COLD
					else:
						terrData[i] = TUNDRA
				elif tempData < fTaigaTemp:
					if plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY_COLD
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY_COLD
					else:
						terrData[i] = TAIGA
				# Instead of harsh thresholds, allow a random deviation chance
				# based on how close to the threshold the rainfall is.
				elif RainData < saltFlatThresLoc and tempData >= fScrubTemp:
					if (RainData < ((1 + random()) * (saltFlatThresLoc - minRain))/2.0 + minRain) and plotData[i] != HILL:
						terrData[i] = SALT_FLATS
					else:
						terrData[i] = DUNES
				elif RainData < dunesThresholLoc and tempData >= fScrubTemp:
					if (RainData < ((1 + random()) * (dunesThresholLoc - saltFlatThresLoc))/2.0 + saltFlatThresLoc):
						terrData[i] = DUNES
					elif plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY_ARID
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY_ARID
					else:
						terrData[i] = DESERT
				elif RainData < desertThreshoLoc and tempData >= fScrubTemp:
					if RainData < ((1 + random()) * (desertThreshoLoc - dunesThresholLoc))/2.0 + dunesThresholLoc:
						terrData[i] = DESERT
					elif plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY_ARID
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY_ARID
					else:
						terrData[i] = SCRUB
				elif RainData < dunesThresholLoc and tempData < fScrubTemp:
					if RainData < ((1 + random()) * (desertThreshoLoc - dunesThresholLoc))/2.0 + dunesThresholLoc:
						terrData[i] = BARREN
					elif plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY
					else:
						terrData[i] = PLAINS
				elif RainData < scrubThresholLoc and tempData >= fScrubTemp:
					if RainData < ((1 + random()) * (scrubThresholLoc - desertThreshoLoc))/2.0 + desertThreshoLoc:
						terrData[i] = SCRUB
					elif plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY
					else:
						terrData[i] = BARREN
				elif RainData < plainThresholLoc:
					if RainData < ((1 + random()) * (plainThresholLoc - scrubThresholLoc))/2.0 + scrubThresholLoc:
						terrData[i] = PLAINS
					elif plotData[i] == HILL and random() <= 2.0 * fRockyPercent:
						terrData[i] = ROCKY
					elif plotData[i] != HILL and random() <= fRockyPercent:
						terrData[i] = ROCKY
					else:
						terrData[i] = GRASS
				elif RainData < grassThresholLoc:
					if RainData < ((1 + random()) * (grassThresholLoc - plainThresholLoc))/2.0 + plainThresholLoc:
						terrData[i] = GRASS
					else:
						terrData[i] = LUSH
				elif random() <= fRockyPercent:
						terrData[i] = ROCKY
				elif RainData < lushThresholdLoc:
					if RainData < ((1 + random()) * (lushThresholdLoc - grassThresholLoc))/2.0 + grassThresholLoc:
						terrData[i] = LUSH
					else:
						terrData[i] = MUDDY
				elif RainData < muddyThresholLoc:
					if RainData < ((1 + random()) * (muddyThresholLoc - lushThresholdLoc))/2.0 + lushThresholdLoc:
						terrData[i] = MUDDY
					elif plotData[i] == HILL:
						terrData[i] = LUSH
					else:
						terrData[i] = MARSH
				else:
					terrData[i] = MARSH

tm = None


class PangaeaBreaker:
	def __init__(self):
		return


	def breakPangeas(self):
		self.iHeight = mc.iHeight
		self.iWidth = mc.iWidth
		self.bPangea = mc.bPangea
		self.bArchipelago = mc.bArchipelago
		fLandPercent = mc.fLandPercent
		iMaxMeteorCount = mc.iMaxMeteorCount
		iMinMeteorSize = mc.iMinMeteorSize
		iMaxMeteorSize = mc.iMaxMeteorSize
		fMinMeteorStr = .6
		fMaxMeteorStr = .2
		iMeteorCount = 0
		self.createDistanceMap()
		self.areaMap = AreaMap()
		self.areaMap.defineAreas(isHmWaterMatch)
		while self.isPangea() and iMeteorCount < iMaxMeteorCount:
			continentList = []
			for a in self.areaMap.areaList:
				if not a.water:
					continentList.append(a)
			#sort all the continents by size, largest first
			continentList.sort(lambda a, b:cmp(b.size, a.size))
			biggestContinentID = continentList[0].ID
			x, y = self.getHighestCentrality(biggestContinentID)
			self.castMeteorUponTheEarth(x, y, iMinMeteorSize, iMaxMeteorSize, fMinMeteorStr, fMaxMeteorStr)
			print "	A meteor struck the Earth at %(x)d, %(y)d!!" % {"x":x,"y":y}
			iMeteorCount += 1
			em.fLandHeight = FindThresholdFromPercent(em.data, fLandPercent)
			self.createDistanceMap()
			self.areaMap.defineAreas(isHmWaterMatch)
		if iMeteorCount > 0:
			print "	%d of maximum %d meteors thrown." % (iMeteorCount, iMaxMeteorCount)
		if self.isPangea():
			print "	Pangea persists."
		else:
			print "	Pangea destroyed."


	def isPangea(self):
		continentList = []
		for a in self.areaMap.areaList:
			if not a.water:
				continentList.append(a)
		fLand = 0.0
		for c in continentList:
			fLand += c.size
		#sort all the continents by size, largest first
		continentList.sort(lambda a, b:cmp(b.size, a.size))
		iBiggest = continentList[0].size
		if self.bArchipelago:
			if 0.16 < iBiggest / fLand:
				return True
		elif 0.58 < iBiggest / fLand:
			return True
		return False


	def castMeteorUponTheEarth(self, x, y, iMinMeteorSize, iMaxMeteorSize, fMinMeteorStr, fMaxMeteorStr):
		self.iMeteorRadius = randint(iMinMeteorSize, iMaxMeteorSize)
		circlePointList = self.getCirclePoints(x, y, self.iMeteorRadius)
		circlePointList.sort(lambda n, m:cmp(n.y, m.y))
		fStrength = uniform(fMaxMeteorStr, fMinMeteorStr)
		for n in xrange(0, len(circlePointList), 2):
			cy = circlePointList[n].y
			if circlePointList[n].x < circlePointList[n + 1].x:
				x1 = circlePointList[n].x
				x2 = circlePointList[n + 1].x
			else:
				x2 = circlePointList[n].x
				x1 = circlePointList[n + 1].x
			self.drawCraterLine(x1, x2, cy, fStrength)


	def drawCraterLine(self, x1, x2, y, fStrength):
		for x in xrange(x1, x2 + 1):
			i = GetIndex(x, y)
			if i == -1:
				continue
			em.data[i] *= fStrength


	def getCirclePoints(self, xCenter, yCenter, radius):
		circlePointList = []
		x = 0
		y = radius
		p = 1 - radius
		self.addCirclePoints(xCenter, yCenter, x, y, circlePointList)
		while (x < y):
			x += 1
			if p < 0:
				p += 2 * x + 1
			else:
				y -= 1
				p += 2 * (x - y) + 1
			self.addCirclePoints(xCenter, yCenter, x, y, circlePointList)
		return circlePointList


	def addCirclePoints(self, xCenter, yCenter, x, y, circlePointList):
		circlePointList.append(CirclePoint(xCenter + x, yCenter + y))
		circlePointList.append(CirclePoint(xCenter - x, yCenter + y))
		circlePointList.append(CirclePoint(xCenter + x, yCenter - y))
		circlePointList.append(CirclePoint(xCenter - x, yCenter - y))
		circlePointList.append(CirclePoint(xCenter + y, yCenter + x))
		circlePointList.append(CirclePoint(xCenter - y, yCenter + x))
		circlePointList.append(CirclePoint(xCenter + y, yCenter - x))
		circlePointList.append(CirclePoint(xCenter - y, yCenter - x))


	def createDistanceMap(self):
		fLandHeight = em.fLandHeight
		self.distanceMap = array('H')
		processQueue = []
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				if em.data[i] < fLandHeight:
					self.distanceMap.append(1000)
				else:
					self.distanceMap.append(0)
					processQueue.append((x, y, i))
		while len(processQueue) > 0:
			x, y, i = processQueue[0]
			del processQueue[0]
			distanceToLand = self.distanceMap[i]
			for direction in xrange(1, 9):
				xx, yy = GetNeighbor(x, y, direction)
				ii = GetIndex(xx, yy)
				if ii >= 0:
					neighborDistanceToLand = self.distanceMap[ii]
					if neighborDistanceToLand > distanceToLand + 1:
						self.distanceMap[ii] = distanceToLand + 1
						processQueue.append((xx, yy, ii))


	def getHighestCentrality(self, ID):
		C = self.createCentralityList(ID)
		C.sort(lambda a, b:cmp(b.centrality, a.centrality))
		return C[0].x, C[0].y


	def createContinentList(self, ID):
		C		= []
		indexMap = []
		gap = int(round(2 + mc.iWorldSize / (1.5 + mc.bArchipelago)))
		n = 0
		i = -1
		for y in xrange(self.iHeight):
			for x in xrange(self.iWidth):
				i += 1
				if y % gap == 0 and x % gap == 0 and self.areaMap.areaID[i] == ID:
					C.append(CentralityScore(x, y))
					indexMap.append(n)
					n += 1
				else:
					indexMap.append(-1)
		n = 0
		for s in C:
			#Check 4 nieghbors
			xx = s.x - gap
			if xx < 0:
				xx = self.iWidth / (gap * gap)
			i = GetIndex(xx, s.y)
			if i != -1 and self.areaMap.areaID[i] == ID:
				s.neighborList.append(indexMap[i])
			xx = s.x + gap
			if xx >= self.iWidth:
				xx = 0
			i = GetIndex(xx, s.y)
			if i != -1 and self.areaMap.areaID[i] == ID:
				s.neighborList.append(indexMap[i])
			yy = s.y - gap
			if yy < 0:
				yy = self.iHeight / (gap * gap)
			i = GetIndex(s.x, yy)
			if i != -1 and self.areaMap.areaID[i] == ID:
				s.neighborList.append(indexMap[i])
			yy = s.y + gap
			if yy > self.iHeight:
				yy = 0
			i = GetIndex(s.x, yy)
			if i != -1 and self.areaMap.areaID[i] == ID:
				s.neighborList.append(indexMap[i])
			n += 1
		return C


	def createCentralityList(self, ID):
		C = self.createContinentList(ID)
		for s in xrange(len(C)):
			S = []
			P = []
			d = []
			delta = []
			sigma = []
			for t in xrange(len(C)):
				sigma.append(0)
				d.append(-1)
				P.append([])
				delta.append(0)
			sigma[s] = 1
			d[s] = 0
			Q = []
			Q.append(s)
			while len(Q) > 0:
				v = Q.pop(0)
				S.append(v)
				for w in C[v].neighborList:
					if d[w] < 0:
						Q.append(w)
						d[w] = d[v] + 1
					if d[w] == d[v] + 1:
						sigma[w] = sigma[w] + sigma[v]
						P[w].append(v)
			while len(S) > 0:
				w = S.pop()
				for v in P[w]:
					delta[v] = delta[v] + (sigma[v]/sigma[w]) * (1 + delta[w])
					if w != s:
						C[w].centrality = C[w].centrality + delta[w]
		return C


pb = None
'''
class DistanceToOcean:
	def __init__(self, x, y, toOceanDist):
		self.x = x
		self.y = y
		self.i = i
		self.toOceanDist = 0
'''
class CirclePoint:
	def __init__(self, x, y):
		self.x = x
		self.y = y


class CentralityScore:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.centrality = 0
		self.neighborList = []


class ContinentMap:
	def __init__(self):
		return


	def generateContinentMap(self):
		print "	Generating Continent Map"
		self.areaMap = AreaMap()
		self.areaMap.defineAreas(em.IsBelowSeaLevel)
		self.newWorldID = self.getNewWorldID()


	def getNewWorldID(self):
		nID = 0
		continentList = []
		for a in self.areaMap.areaList:
			if not a.water:
				continentList.append(a)
		# If this was the only continent than we have a pangaea. Oh well.
		if len(continentList) == 1:
			return -1
		bWrapX = mc.bWrapX
		bWrapY = mc.bWrapY
		iHeight = mc.iHeight
		iWidth = mc.iWidth
		fLand = 0.0
		for c in continentList:
			fLand += c.size
		# Sort all the continents by size, largest first.
		continentList.sort(lambda a, b:cmp(b.size, a.size))
		#now remove a percentage of the landmass to be considered 'Old World'
		#biggest continent is automatically 'Old World'
		oldWorldSize = continentList[0].size
		oldWorldAvgX = continentList[0].avgX
		oldWorldAvgY = continentList[0].avgY
		del continentList[0]
		#get the next largest continent and temporarily remove from list
		#add it back later and is automatically 'New World'
		mainNewWorld = continentList[0]
		del continentList[0]
		#LM - sort list by proximity
		for c in continentList:
			minX = oldWorldAvgX - c.avgX
			minY = oldWorldAvgY - c.avgY
			if minX < 0:
				minX *= -1
			if minY < 0:
				minY *= -1
			if bWrapX and minX > iWidth - minX:
				minX = iWidth - minX
			if bWrapY and minY > iHeight - minY:
				minY = iHeight - minY
			c.distance = sqrt(minX ** 2 + minY ** 2)
		continentList.sort(lambda a, b:cmp(a.distance, b.distance))
		for n in xrange(len(continentList)):
			oldWorldSize += continentList[0].size
			del continentList[0]
			if oldWorldSize / fLand > 0.6:
				break
		# Add back the mainNewWorld continent.
		continentList.append(mainNewWorld)
		# What remains in the list will be considered 'New World'.
		# Get ID for the next continent, we will use this ID for 'New World' designation.
		nID = continentList[0].ID
		del continentList[0] # Delete to avoid unnecessary overwrite.
		# Now change all the remaining continents to also have nID as their ID.
		for i in xrange(mc.iArea):
			for c in continentList:
				if c.ID == self.areaMap.areaID[i]:
					self.areaMap.areaID[i] = nID
		return nID

coMa = ContinentMap()


class LakeMap:
	def __init__(self):
		return

	def generateLakeMap(self):
		print "	Adding lakes"
		iWidth	= mc.iWidth
		iHeight = mc.iHeight
		iArea	= mc.iArea
		# Make a list of all the pits that lakes can expand from, ordered randomly.
		# Use this oppertunity to create an 2x2 average rainfall map:
		# 	We use S, E and SE for the 2x2 area as it will be used for the river map;
		# 	rivers exist east and south of plots in the plot to plot intersection.
		self.avrRainfallMap2x2 = avrRainMap = array('f', [0.0] * iArea)
		lakePitList = []
		fLakeRainMax = 0
		relAltMap = em.relAltMap3x3
		altitude = em.data
		fLandHeight = em.fLandHeight
		rainData = cm.RainfallMap.data
		plotData = tm.plotData
		WATER		= mc.WATER
		DESERT		= mc.DESERT
		DUNES		= mc.DUNES
		SALT_FLATS	= mc.SALT_FLATS
		ICE			= mc.ICE
		FROST		= mc.FROST
		TUNDRA	 	= mc.TUNDRA
		LUSH		= mc.LUSH
		MARSH		= mc.MARSH
		MUDDY		= mc.MUDDY
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if relAltMap[i] == -1.0:
					lakePitList.append((x, y, i))
				total = 0.0
				count = 0.0
				if plotData[i] != WATER:
					for yy in xrange(y - 1, y + 1):
						for xx in xrange(x, x + 2):
							ii = GetIndex(xx, yy)
							if ii >= 0 and plotData[ii] != WATER:
								total += rainData[ii]
								count += 1.0
					avrRainMap[i] = total / count
					# if Lake pit, keep track of rainiest tile for normalization later
					if relAltMap[i] == -1.0 and avrRainMap[i] > fLakeRainMax:
						fLakeRainMax = avrRainMap[i]
		shuffle(lakePitList)
		lakeAreaMap	= AreaMap()
		self.lakeData = array('b', [0] * iArea)
		iTargetLakeTiles = int(round(iArea * mc.fLandPercent * mc.fLakesPercent))
		iTotalLakeTilesPlaced = iLakePitsUsed = iInvalidLakePits = 0
		iMaxLakeSize = mc.iMaxLakeSize
		fLakeSizeMinPercent = mc.fLakeSizeMinPercent
		fLakeSizeModChance = mc.fLakeSizeFactorPercent
		fHeatMod = mc.fHeatLakeFactor
		fColdMod = mc.fColdLakeFactor
		fWetMod = mc.fWetLakeFactor
		fAltitudeMinFactor = mc.fAltitudeMinFactor
		fRainMinFactor = mc.fRainMinFactor
		tData = tm.terrData
		print "	Desire %d lake tiles from %d pits" % (iTargetLakeTiles, len(lakePitList))
		# Find lake starting spots, and expand outward based on factors present at lakepit
		for x, y, i in lakePitList:
			if self.lakeData[i] == 0 and iTotalLakeTilesPlaced < iTargetLakeTiles:
				# Terrain Mod; lakesize adjusted by starting terrain type.
				HERE = tData[i]
				if HERE == DESERT or HERE == DUNES or HERE == SALT_FLATS:
					fTerrainMod = fHeatMod
				elif HERE == ICE or HERE == TUNDRA or HERE == FROST:
					fTerrainMod = fColdMod
				elif HERE == LUSH or HERE == MARSH or HERE == MUDDY:
					fTerrainMod = fWetMod
				else:
					fTerrainMod = 1.0
				# Altitude Mod; smaller lakes at higher altitudes as a linear func of % of way to max land height (1.0) from altitude
				fAltitudeMod = LinearMapping(fLandHeight, 1.0, altitude[i], fAltitudeMinFactor, 1)
				# Rain Mod; lakesize adjusted by rainfall normalized across potential lakepits, renormalized to fRainMinFactor.
				fRainMod = LinearMapping(0, 1, (avrRainMap[i]/fLakeRainMax), fRainMinFactor, 1)
				# Size Mod; randomly reduces lake size based on custom values set.
				if random() < fLakeSizeModChance:
					fSizeMod = uniform(fLakeSizeMinPercent, 1.0)
				else:
					fSizeMod = 1.0

				# How big we expect a lake starting at this tile to grow to
				iTargetLakeSize = int(round(iMaxLakeSize * fRainMod * fTerrainMod * fAltitudeMod * fSizeMod))
				
				# Generate lake, so long as isn't too big
				if iTargetLakeSize > 0 and (iTargetLakeSize <= iTargetLakeTiles - iTotalLakeTilesPlaced):
					# print "	Starting lake at (%d, %d) of target size: %d" % (x, y, iTargetLakeSize)
					# print "	fRain: %f, fTerrain: %f, fAltitude: %f, fSize: %f" % (fRainMod, fTerrainMod, fAltitudeMod, fSizeMod)
					iLakeTilesAdded = self.expandLake(x, y, i, lakeAreaMap, iTargetLakeSize, WATER)
					if iLakeTilesAdded > 0:
						iTotalLakeTilesPlaced += iLakeTilesAdded
						iLakePitsUsed += 1
						if iLakeTilesAdded != iTargetLakeSize:
							# print "	Tried to add %i tiles from lake started at (%i, %i), instead added %i!" % (iTargetLakeSize, x, y, iLakeTilesAdded)
							pass
					else:
						iInvalidLakePits += 1
				elif iTargetLakeSize == 0:
					iInvalidLakePits += 1
			if iTotalLakeTilesPlaced >= iTargetLakeTiles:
				break
		if iTotalLakeTilesPlaced < iTargetLakeTiles: #if failed to place lake tiles up to target
			print "	Ran out of valid lake pits!"
		print "	Made %i water tiles (of %i desired) across %i lake pits used of %i total (%i invalid starting placements)." \
			% (iTotalLakeTilesPlaced, iTargetLakeTiles, iLakePitsUsed, len(lakePitList), iInvalidLakePits)
		if mc.bWrapX:
			# Avoid Water-plane graphical glitch at the map edges.
			self.avoidWrapWaterGlitch(iWidth, iHeight, WATER)
		self.reassignSalinity(lakeAreaMap, WATER)
		self.defineWaterTerrain(iWidth, iHeight, iArea, em.fLandHeight, WATER)


	def expandLake(self, x, y, i, lakeAreaMap, iLakeSize, WATER):
		class LakePlot:
			def __init__(self, x, y, i, fHeight):
				self.x = x
				self.y = y
				self.i = i
				self.fHeight = fHeight

		plotData = tm.plotData
		relAltMap = em.relAltMap3x3
		thePlot = LakePlot(x, y, i, em.data[i])

		# Making these global to the LakeMap class is necessary for the weightedDistance key function to work properly. I think.
		self.lakeCenter = (x, y)
		self.thisLake = []

		lakeNeighbors = []
		iPlacedTiles = 0 # Explicitly keep track of how many tiles we place, this value will be returned
		checkedPlotDict = {i:1} # Keeping track of tiles to avoid excess checking in some cases w/very large lakes
		bHarbor = False
		harborList = []

		# Check if start-point is valid (not on or adjacent to ocean)
		for dir in xrange(0, 9):
			xx, yy = GetNeighbor(x, y, dir)
			ii = GetIndex(xx, yy)
			if ii >= 0 and plotData[ii] == WATER and self.lakeData[ii] != 1:
				print "	Skipping: Plot (%i, %i) has ocean adjacency at (%i, %i)" % (x, y, xx, yy)
				return iPlacedTiles

		# Grow lake, in 3 main parts. 1) Add currently selected tile, 2) find new potential neighbors, 3) sort and select best neighbor to grow to.
		while iLakeSize > 0:

			# Part 1, add current tile "thePlot" to thisLake. Has a chance of growing an already existing lake, if not spawning with 4 cardinal adjacent lake tiles.
			i = thePlot.i
			if plotData[i] != WATER:
				iLakeSize -= 1
				iPlacedTiles += 1
				plotData[i] = WATER
			checkedPlotDict[i] = 1
			self.updateLake(lakeAreaMap, i) # This automatically merges any lakes touching thePlot into thisLake

			# Part 2, look at new neighbors (xx, yy, ii) and filter for list of potential tiles to grow to. Merge/make harbor if necessary.
			for dir1 in xrange(1, 9):
				xx, yy = GetNeighbor(thePlot.x, thePlot.y, dir1)
				ii = GetIndex(xx, yy)
				if ii in checkedPlotDict or ii < 0:
					continue
				# Diagonal tiles are only looked at for harbor purposes, so don't count them as being checked/added to lakeNeighbors
				if dir1 < 6:
					checkedPlotDict[ii] = 1

				# If we've directly touched water, it's either our own lake (already merged), or ocean.
				if plotData[ii] == WATER and dir1 < 6:
					if self.lakeData[ii] == 1: # This has already been merged in part 1 self.updateLake, but didn't grab the checked plot
						checkedPlotDict[ii] = 1
						continue
					else: # This is ocean, which means we no longer should have a lake. Convert to ocean and stop expanding.
						for index in self.thisLake:
							self.lakeData[index] = -1
						# print "	Lake found ocean (was harbor?: %i) at (%i, %i)" % (bHarbor, xx, yy)
						return iPlacedTiles # We managed to place >1 tiles, even if they did become ocean
				# If direct neighbor is land (and we aren't making a harbour) add to list of neighbors to grow next
				elif dir1 < 6:
					lakeNeighbors.append(LakePlot(xx, yy, ii, em.data[ii]))
				# If we're diagonally touching water on this plot, either expand toward it if it's saltwater, or take it as neighbor if have none.
				elif plotData[ii] == WATER:
					if not self.lakeData[ii] and random() < 0.5:
						harbor1index = GetIndex(thePlot.x, yy)
						harbor2index = GetIndex(xx, thePlot.y)
						harbor1plot  = LakePlot(thePlot.x, yy, harbor1index, em.data[harbor1index])
						harbor2plot  = LakePlot(xx, thePlot.y, harbor2index, em.data[harbor2index])
						harborList.extend((harbor1plot, harbor2plot))
						thePlot = choice(harborList)
						if iLakeSize == 0:
							print "	Emergency lake growth at (%i, %i) to make harbor!" % (thePlot.x, thePlot.y)
							iLakeSize += 1
						bHarbor = True
					# Case where lake spawns on another lake and can't find adjacent neighbors, try looking a bit further
					elif self.lakeData[ii] and len(lakeNeighbors) == 0:
						lakeNeighbors.append(LakePlot(xx, yy, ii, em.data[ii]))

			# Part 3, figure out next best tile to grow if possible, and set that tile as next to expand into for following loop cycle			
			if bHarbor:
				continue
			elif iLakeSize <= 0 or len(lakeNeighbors) == 0:
				return iPlacedTiles
			
			bHarbor = False
			if len(lakeNeighbors) > 1:
				lakeNeighbors.sort(key=self.weightedDistance, reverse=True) # Sort from high score to low
			thePlot = lakeNeighbors.pop(0)

		print "	Unexpected escape from expandLake! Returning lake grown to size %i, with %i placed tiles" % (len(self.thisLake), iPlacedTiles)
		return iPlacedTiles


	def updateLake(self, lakeAreaMap, newPlotIndex):
		"""
		Updates self.thisLake and self.lakeCenter
		Somewhat expensive rebuild of lakeAreaMap, but we want the updated average position of the lake and to take advantage
		of the automatic merging it ends up doing, now that merging above global maxlakesize is acceptable.
		"""

		# Redefine all areas on map that match lakeData criteria. Could be cheaper, but eh. Automatically merges applicable lakes.
		self.lakeData[newPlotIndex] = 1
		lakeAreaMap.defineAreas(self.matchLake)
		# print "	newPlotIndex: %i" % newPlotIndex
		# the ID value of the Area class buried in lakeAreaMap is what we want for updating thisLake now, and Area.avgX, Area.avgY for later sorting
		lakeArea = lakeAreaMap.getAreaByPlotIndex(newPlotIndex)
		self.lakeCenter = (lakeArea.avgX, lakeArea.avgY)
		# print "	New center after update: (%f, %f), size: %i" % (lakeArea.avgX, lakeArea.avgY, lakeArea.size)

		# Rebuild thisLake by looking at index of tiles that match areaID value, for areaID of our new lakeArea.
		# This merges lake tiles that were adjacent to newPlotIndex into thisLake
		self.thisLake = [plotIndex for plotIndex, areaID in enumerate(lakeAreaMap.areaID) if areaID == lakeArea.ID]

		# print "Lake tiles are:"
		# print [GetCoordFromIndex(i) for i in thisLake]


	def weightedDistance(self, neighborPlot):
		"""
		Takes a LakePlot object, finds how likely it should be picked next to expand to given the current thisLake
		"""
		pass
		maxRelativeRadius = 4 # Maximum maximum relative radius a lake can reach compared to expected shape. Greater value -> greater effective fEccentricity value
		fEccentricity = mc.fLakeEccentricity
		fLandHeight = em.fLandHeight
		currLakeSize = len(self.thisLake)

		expectedlakeRadius = sqrt((currLakeSize+1) / pi)
		neighborPlotRadius = self.calculateCenterPlotRadius(neighborPlot.i)
		radiusRatio = neighborPlotRadius / expectedlakeRadius

		# 1 at water level, 0 at max altitude
		heightDiffPercent = LinearMapping(fLandHeight, 1.0, neighborPlot.fHeight, 1, 0)

		# 1 at or below expected radius, linearally decreasing to 0 at maxRelativeRadius
		radialDistPercent = LinearMapping(1, maxRelativeRadius, radiusRatio, 1, 0) # CHANGE TO NOT NORMALIZED; say 3 tile range? 

		# This is our final score for selecting the tile or not.
		weightedScore = (fEccentricity * heightDiffPercent) + (1 - fEccentricity) * radialDistPercent

		x, y = GetCoordFromIndex(neighborPlot.i)
		# print "		Neighbor (%i, %i, alt: %f, rad: %f) has score: %f" % (x, y, neighborPlot.fHeight, neighborPlotRadius, weightedScore)
		# print "		Breakdown:: heightDif: %f, radialDist: %f" % (heightDiffPercent, radialDistPercent)
		# print "		Breakdown:: currLakeSize: %i, expectedR: %f, plotR: %f" % (currLakeSize, expectedlakeRadius, neighborPlotRadius)

		return weightedScore

	def calculateCenterPlotRadius(self, plotIndex):
		"""
		This is basically plotDistance from CvGameCoreUtils.h (but for float values) with a fixed lakeCenter arg
		"""
		x, y = GetCoordFromIndex(plotIndex)
		bWrapX, bWrapY = mc.bWrapX, mc.bWrapY
		iWidth, iHeight = mc.iWidth, mc.iHeight

		xDist = self.calculateCoordDistance(self.lakeCenter[0], x, iWidth , bWrapX)
		yDist = self.calculateCoordDistance(self.lakeCenter[1], y, iHeight, bWrapY)

		return sqrt(xDist ** 2 + yDist ** 2)

	def calculateCoordDistance(self, center, target, iMaxRange, bWrap):
		if bWrap and (abs(target - center) > iMaxRange / 2):
			return iMaxRange - abs(target - center)
		else:
			return abs(target - center)


	# Ensures the tile type at edges of wrapped world match, so no visible seam is drawn (fault of graphical engine or something)
	# Note that this will potentially cause a lake to touch ocean, so another check/update is included in reassignSalinity to fix
	def avoidWrapWaterGlitch(self, iWidth, iHeight, WATER):
		plotData = tm.plotData
		terrData = tm.terrData

		# Check X wrap, set plot and terrain type to be same on left and right edges
		for y in xrange(iHeight):
			xWestEdgeID = y * iWidth
			xEastEdgeID = xWestEdgeID + iWidth - 1
			if (
				WATER in (plotData[xEastEdgeID], plotData[xWestEdgeID])
				and
				plotData[xEastEdgeID] != plotData[xWestEdgeID]
			):
				if plotData[xEastEdgeID]:
					plotData[xWestEdgeID] = plotData[xEastEdgeID]
					terrData[xWestEdgeID] = terrData[xEastEdgeID]
				else:
					plotData[xEastEdgeID] = plotData[xWestEdgeID]
					terrData[xEastEdgeID] = terrData[xWestEdgeID]
		# Check Y wrap
		if mc.bWrapY:
			for southEdgeID in xrange(iWidth):
				northEdgeID = southEdgeID + (iHeight - 1) * iWidth
				if (
					WATER in (plotData[southEdgeID], plotData[northEdgeID])
					and
					plotData[southEdgeID] != plotData[northEdgeID]
				):
					if plotData[southEdgeID]:
						plotData[northEdgeID] = plotData[southEdgeID]
						terrData[northEdgeID] = terrData[southEdgeID]
					else:
						plotData[southEdgeID] = plotData[northEdgeID]
						terrData[southEdgeID] = terrData[northEdgeID]


	def reassignSalinity(self, lakeAreaMap, WATER):
		"""
		TODO: assign lakes to be salt or fresh based on final size, and fBlurOnset/fBlurHarshness
		"""
		return
		waterMap = AreaMap()
		waterMap.defineAreas(self.matchWater)
		bUpdatedLake = False

		# Loop thru area IDs of lake area; check if size is same as waterMap containing that tile.
		# If lake is smaller (or larger???) than water, then delete that lake
		for lakeArea in lakeAreaMap.areaList:
			lakeCenterX = int(round(lakeArea.avgX))
			lakeCenterY = int(round(lakeArea.avgY))
			lakeCenterIndex = GetIndex(lakeCenterX, lakeCenterY)

			# NOTE: This block is somewhat untested due to low liklihood of it occurring...
			# If the size of the lake is not the same as the size of the water body containing it, that means the lake has touched ocean
			# (likely caused by avoidWrapWaterGlitch; either a lake tile expanded, or ocean tile expanded to touch the either)
			# So, we need to remove that lake's data from self.lakeData
			if lakeArea.size != waterMap.getAreaByPlotIndex(lakeCenterIndex).size:
				print "	Lake/ocean touch detected near (%i, %i)! Fixing..." % (lakeCenterX, lakeCenterY)
				matchingLakeArea = lakeAreaMap.getAreaMapByID(lakeArea.ID)
				print matchingLakeArea
				# Look
				self.lakeData = [self.lakeData[i] - matchingLakeArea[i] for i in xrange(mc.iArea)]
				print self.lakeData
				bUpdatedLake = True

		if bUpdatedLake:
			lakeAreaMap.defineAreas(self.matchLake)


		# Match the ID of the erronous lake; collect the index values, and match against the lakeData map

		########################
		# the ID value of the Area class buried in lakeAreaMap is what we want for updating thisLake now, and Area.avgX, Area.avgY for later sorting
		lakeArea = lakeAreaMap.getAreaByPlotIndex(newPlotIndex)
		self.lakeCenter = (lakeArea.avgX, lakeArea.avgY)
		# print "	New center after update: (%f, %f), size: %i" % (lakeArea.avgX, lakeArea.avgY, lakeArea.size)

		# Rebuild thisLake by looking at index of tiles that match areaID value for areaID of our new lake tile.
		# This merges lake tiles that were adjacent to newPlotIndex into thisLake
		self.thisLake = [plotIndex for plotIndex, areaID in enumerate(lakeAreaMap.areaID) if areaID == lakeArea.ID]
		#################

		# Then, pass the area of each area ID one at a time to salinityBlurring. Depending on outcome, update the plots of lakeArea/lakeData accordingly

		# currentLakeID = lakeAreaMap.areaID[i]

	def salinityBlurring(self, waterSize, fModifier):
		"""
		Takes in the size of a body of water and any modifiers
		Returns 1 for lake, 0 for ocean
		"""
		iMaxLakeSize = mc.iMaxLakeSize
		fBlurOnset = mc.fBlurOnset
		fBlurHarshness = mc.fBlurHarshness

		# Look at how much larger or smaller we are than the adjusted max lake size
		if fBlurOnset == 0:
			return 0 # No freshwater water terrain anywhere on map
		else:
			fLakeSizeRatio = waterSize / (fBlurOnset * iMaxLakeSize)

		if fLakeSizeRatio < 1: # Adjust (0, 1) range onto (-inf, 0); 1/2 -> -2, 1/3 -> -3, etc
			fLakeSizeRatio = -1.0 / fLakeSizeRatio
		
		# Logistic func; takes fLakeSizeRatio in (-inf, inf) returning value in (-1, 1).
		# 0 fLakeSizeRatio returns 0.5 lakeChance, fBlurHarshness determines climb rate to either side
		lakeChance = 1.0 / (1 + e ** (-fBlurHarshness * fLakeSizeRatio))

		if random() < lakeChance:
			return 1
		else:
			return 0


	def matchLake(self, x, y):
		return self.lakeData[GetIndex(x, y)] == 1

	def matchWater(self, x, y):
		return tm.plotData[GetIndex(x, y)] == mc.WATER


	def defineWaterTerrain(self, iWidth, iHeight, iArea, fLandHeight, WATER):
		print "	Defining Water Terrain"
		plotData = tm.plotData
		terrData = tm.terrData
		fPolarLat	= mc.fPolarLat
		fTropicLat	= mc.fTropicLat
		climateList = []
		latFactor = 2.0 / (iHeight - 1.0)
		# Map the climate zones.
		i = -1
		for y in xrange(iHeight):
			lat = y * latFactor - 1.0
			if lat >= fPolarLat or -fPolarLat >= lat:
				climate = -1
			elif lat >= -fTropicLat and fTropicLat >= lat:
				climate = 1
			else:
				climate = 0
			climateList = climateList + [climate] * iWidth
		bDefined = array('H', [0] * iArea)
		lakeData = self.lakeData
		# First define coast and shore.
		COAST		= mc.COAST
		COAST_POL	= mc.COAST_POL
		COAST_TROP	= mc.COAST_TROP
		LAKE_SHORE	= mc.LAKE_SHORE
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if not plotData[i]:
					for dir in xrange(1, 9):
						xx, yy = GetNeighbor(x, y, dir)
						ii = GetIndex(xx, yy)
						if ii >= 0 and plotData[ii]:
							if lakeData[i] != 1:
								bDefined[i] = COAST
								if not climateList[i]:
									terrData[i] = COAST
								elif climateList[i] == 1:
									terrData[i] = COAST_TROP
								else:
									terrData[i] = COAST_POL
							else:
								bDefined[i] = LAKE_SHORE
								if not climateList[i]:
									terrData[i] = LAKE_SHORE
								elif climateList[i] == 1:
									terrData[i] = LAKE_SHORE
								else:
									terrData[i] = LAKE_SHORE
		# Then define these:
		OCEAN		= mc.OCEAN
		OCEAN_POL	= mc.OCEAN_POL
		OCEAN_TROP	= mc.OCEAN_TROP
		SEA			= mc.SEA
		SEA_POL		= mc.SEA_POL
		SEA_TROP	= mc.SEA_TROP
		SEA_DEEP	= mc.SEA_DEEP
		SEA_DEEP_P	= mc.SEA_DEEP_P
		SEA_DEEP_T	= mc.SEA_DEEP_T
		LAKE		= mc.LAKE
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if not (plotData[i] or bDefined[i]):
					if lakeData[i] == 1:
						bDefined[i] = LAKE
						if not climateList[i]:
							terrData[i] = LAKE
						elif climateList[i] == 1:
							terrData[i] = LAKE
						else:
							terrData[i] = LAKE
					else:
						for dir in xrange(1, 9):
							xx, yy = GetNeighbor(x, y, dir)
							ii = GetIndex(xx, yy)
							if ii >= 0 and 	bDefined[ii] == COAST:
								bDefined[i] = SEA
								if em.data[i] < fLandHeight * 0.75:
									if not climateList[i]:
										terrData[i] = SEA_DEEP
									elif climateList[i] == 1:
										terrData[i] = SEA_DEEP_T
									else:
										terrData[i] = SEA_DEEP_P
								else:
									if not climateList[i]:
										terrData[i] = SEA
									elif climateList[i] == 1:
										terrData[i] = SEA_TROP
									else:
										terrData[i] = SEA_POL
								break
						if not bDefined[i]:
							bDefined[i] = OCEAN
							if not climateList[i]:
								terrData[i] = OCEAN
							elif climateList[i] == 1:
								terrData[i] = OCEAN_TROP
							else:
								terrData[i] = OCEAN_POL
		# Define trenches in the end.
		TRENCH		= mc.TRENCH
		TRENCH_POL	= mc.TRENCH_POL
		TRENCH_TROP	= mc.TRENCH_TROP
		fTrenchEle = em.fTrenchEle
		trenchList = []
		bAttenuate = mc.bAttenuate
		fMinY = 0.05 * iHeight
		fMaxY = 0.95 * iHeight
		i = -1
		for y in xrange(iHeight):
			if bAttenuate:
				if y < fMinY:
					i += iWidth
					continue
				elif fMaxY <= y:
					break
			for x in xrange(iWidth):
				i += 1
				if em.data[i] < fTrenchEle:
					if bDefined[i] == OCEAN:
						trenchList.append((x, y, i))
		shuffle(trenchList)
		iNumTrenches = em.iNumTrenches
		print "	Desired number of trenches: %d" % em.iNumTrenches
		print "	Available trench spots: %d" % len(trenchList)
		fTrenchExpCha = 0.4 - mc.iWorldSize / 24.0
		nt = 0
		while len(trenchList) > 0 and iNumTrenches != nt:
			x, y, i = trenchList.pop()
			if bDefined[i] == TRENCH:
				continue
			n = 0
			bGoodToGo = False
			for dir in xrange(1, 9):
				xx, yy = GetNeighbor(x, y, dir)
				ii = GetIndex(xx, yy)
				if ii >= 0 and bDefined[ii] == OCEAN:
					n += 1
				if n > 4:
					bGoodToGo = True
					break
			if bGoodToGo:
				nt += 1
				trenchExpPlots = []
				iTrenchPlots = 0
				while True:
					if not climateList[i]:
						terrData[i] = TRENCH
					elif climateList[i] == 1:
						terrData[i] = TRENCH_TROP
					else:
						terrData[i] = TRENCH_POL
					bDefined[i] = TRENCH
					SurTr = 0
					iTrenchPlots += 1
					if iTrenchPlots == 1 or random() > fTrenchExpCha * iTrenchPlots:
						for dir in xrange(1, 9):
							xx, yy = GetNeighbor(x, y, dir)
							ii = GetIndex(xx, yy)
							if ii >= 0:
								if bDefined[ii] == OCEAN:
									trenchExpPlots.append((xx, yy, ii))
								elif bDefined[i] == TRENCH:
									SurTr += 1
									if SurTr > 2:
										break
						if SurTr > 2:
							break
						if len(trenchExpPlots) > 2:
							shuffle(trenchExpPlots)
							x, y, i = trenchExpPlots.pop()
							continue
					break
		print "	Trenches made: %d" % nt

lm = None


# Now that directions N,S,E,W are important, there is one thing helpfull to know.
# That the X and Y coordinates are zero in the SW corner.
class RiverMap:
	def __init__(self):
		return


	def generateRiverMap(self):
		print "	Generating River Map"
		iWidth	= mc.iWidth
		iHeight = mc.iHeight
		iArea	= mc.iArea
		# The avrRelAltMap is the relative altitude average based on the em.relAltMap3x3.
		# The drainageMap keeps track of accumulated rainfall along a river based on the lm.avrRainfallMap2x2.
		# The flowMap stores the direction that fresh water flows in from a plot.

		avrRelAltMap3x3	= array('f', [0.0] * iArea)
		drainageMap		= array('f', [0.0] * iArea)
		noMoreFlow		= array('b', [0]   * iArea) # 1 and minus 1 means coastal plot, 2 means a plot where the river split, and 3 means the plot where the river start.
		flowMap			= [(-1, -1)] * iArea
		self.riverMap	= [(-1, -1)] * iArea

		# Create a relative altitude average with a few denotation values:
		#	|O X O|
		#	|X C W|
		#	|O W W|
		# If C is PEAK, relative height average is set to 1.0 for C.
		# If C is WATER, relative height average is set to -1.0 for C.
		# O is ignored for all purposes; if W is water the average relative height of C is set to -1.0
		# The relative height is taken from W that is not water, X and C; if X is water they count as 0.0 towards the total height.
		PEAK  = mc.PEAK
		WATER = mc.WATER
		ICE	  = mc.ICE
		bWrapX = mc.bWrapX
		bWrapY = mc.bWrapY
		dl = (mc.iWorldSize + 3) / 3
		plotData = tm.plotData
		terrData = tm.terrData
		relAltMap = em.relAltMap3x3
		shoreList = []
		aList = []
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if not plotData[i] or plotData[i] == PEAK or terrData[i] == ICE or (not bWrapX and x == iWidth - 1) or not (bWrapY or y):
					noMoreFlow[i] = -1
					continue
				count = 0.0
				total = 0.0
				Coord = [(x, y), (x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1), (x + 1, y - 1)]
				for n in xrange(6):
					xx, yy = Coord.pop()
					ii = GetIndex(xx, yy)
					if ii >= 0:
						if not plotData[ii]:
							if xx == x - 1 or yy == y + 1:
								count += 1.0
								# Denote the water border to the north/west.
								noMoreFlow[i] = 1
							else:
								# Denote the water border to the south/east.
								# This overide the north/west ocean border denotation.
								noMoreFlow[i] = -1
								break
						else:
							count += 1.0
							total += relAltMap[ii]
				if noMoreFlow[i]:
					bValid = True
					for yy in xrange(y - 3, y + 4):
						for xx in xrange(x - 3, x + 4):
							ii = GetIndex(xx, yy)
							if ii in aList:
								bValid = False
								break
						if not bValid:
							break
					if bValid:
						shoreList.append([x, y, i])
						aList.append(i)
				if noMoreFlow[i] != -1.0:
					avrRelAltMap3x3[i] = total/count
		N = mc.N
		S = mc.S
		W = mc.W
		E = mc.E
		# Draw imaginary rivers inland from the valid shore plots
		avrRain = lm.avrRainfallMap2x2
		aRiverList = []
		aSourceList = []
		for x, y, i in shoreList:
			if i == -1:
				continue
			aList = []
			bMerge = True
			queueList = []
			# We need to add the drainage to this type of shore.
			if noMoreFlow[i] == 1:
				# For each place that is lower, add it to a list to be randomly chosen as the drainage.
				drainList = []
				count = 0
				ii = GetIndex(x, y + 1)
				if ii >= 0 and not tm.plotData[ii]:
					drainList.append(N)
					count += 1
				iii = GetIndex(x - 1, y)
				if iii >= 0 and not tm.plotData[iii]:
					drainList.append(W)
					count += 1
				if count == 2:
					if random() > 0.7:
						flowMap[i] = drainList[0], drainList[1]
					else:
						shuffle(drainList)
						flowMap[i] = drainList[0], -1
				elif count == 1:
					flowMap[i] = drainList[0], -1
				elif ii >= 0 or iii >= 0:
					print "logical error in river flow 1 - BUG"
				iRestrict = 0
			else:
				iRestrict = 1
			# print "	Generating River Map Debug Point 1"
			loop = -1
			while True:
				loop += 1
				drainList = []
				fLowestRelAlt = 999.0
				fCurRelAlt = avrRelAltMap3x3[i]
				# For each place that is higher, add it to a list to be chosen as the upstream path(s).
				count = 0
				ii = GetIndex(x, y + 1)
				fRelHeight = avrRelAltMap3x3[ii]
				if ii >= 0 and not noMoreFlow[ii] and ii not in aList and fRelHeight > fCurRelAlt:
					drainList.append((x, y + 1, ii, S))
					iLowest = count
					fLowestRelAlt = fRelHeight
					count += 1
				ii = GetIndex(x, y - 1)
				fRelHeight = avrRelAltMap3x3[ii]
				if ii >= 0 and not noMoreFlow[ii] and ii not in aList and fRelHeight > fCurRelAlt:
					drainList.append((x, y - 1, ii, N))
					if fRelHeight < fLowestRelAlt:
						fLowestRelAlt = fRelHeight
						iLowest = count
					count += 1
				ii = GetIndex(x - 1, y)
				fRelHeight = avrRelAltMap3x3[ii]
				if ii >= 0 and not noMoreFlow[ii] and ii not in aList and fRelHeight > fCurRelAlt:
					drainList.append((x - 1, y, ii, E))
					if fRelHeight < fLowestRelAlt:
						fLowestRelAlt = fRelHeight
						iLowest = count
					count += 1
				ii = GetIndex(x + 1, y)
				fRelHeight = avrRelAltMap3x3[ii]
				if ii >= 0 and not noMoreFlow[ii] and ii not in aList and fRelHeight > fCurRelAlt:
					drainList.append((x + 1, y, ii, W))
					if fRelHeight < fLowestRelAlt:
						iLowest = count
					count += 1
				# Did we find a higher altitude?
				if count:
					x, y, i, dir1 = drainList[iLowest]
					aList.append(i)
					del drainList[iLowest]
					if drainList and iRestrict <= loop:
						iRestrict = loop + 2
						shuffle(drainList)

						xx, yy, ii, dir2 = drainList[0]
						aList.append(ii)
						if flowMap[ii][0] == -1:
							flowMap[ii] = dir2, -1
							bDone = True
						elif flowMap[ii][1] == -1:
							aList += aRiverList
							bMerge = False
							flowMap[ii] = flowMap[ii][0], dir2
							noMoreFlow[ii] = 2
							bDone = True
						else:
							bDone = False
							print "logical error in river flow 2 - BUG"
						if bDone:
							queueList.append((xx, yy, ii))

					if flowMap[i][0] == -1:
						flowMap[i] = dir1, -1
					elif flowMap[i][1] == -1:
						aList += aRiverList
						bMerge = False
						flowMap[i] = flowMap[i][0], dir1
						noMoreFlow[i] = 2
					else:
						print "logical error in river flow 3 - BUG"
				else: # Highest altitude reached.
					if not loop and not iRestrict:
						flowMap[i] = -1, -1
					elif not noMoreFlow[i]:
						noMoreFlow[i] = 3
						fPriority = avrRelAltMap3x3[i] * avrRain[i]
						aSourceList.append((fPriority, x, y, i))
					if not queueList:
						if bMerge:
							aRiverList += aList
						else:
							aRiverList = list(aList)
						break
					else:
						x, y, i = queueList.pop()
						iRestrict = loop + 2
		# Sort the river source list by declining priority.
		from operator import itemgetter
		aSourceList.sort(key=itemgetter(0), reverse=True)
		# Now use the flowMap as a guide to distribute average rainfall.
		# Wherever the most rainfall ends up is where the rivers will be.
		plainsThreshold	= tm.plainsThreshold
		fRiverThreshold = mc.fRiverThreshold
		queueList = []
		aList = []
		for iLength, x, y, i in aSourceList:

			flow1, flow2 = flowMap[i]
			if flow1 < 1: continue

			iLength = 0
			drainageMap[i] += avrRain[i]
			if drainageMap[i] >= fRiverThreshold:
				iLength += 1
			xx = x
			yy = y
			fCarryOver = drainageMap[i]
			idxPrev = i
			# print "	Generating River Map Debug Point 2"
			while True:
				if flow1 == N:
					yy += 1
				elif flow1 == S:
					yy -= 1
				elif flow1 == W:
					xx -= 1
				elif flow1 == E:
					xx += 1
				else:
					print "Drainage logical error 1 - bug"
					break
				ii = GetIndex(xx, yy)
				if ii >= 0:
					# Check if merging with an already established river
					if drainageMap[ii] >= fRiverThreshold:
						if fCarryOver < fRiverThreshold and avrRain[i] >= plainsThreshold:
							drainageMap[idxPrev] = fRiverThreshold
						aList.append((xx, yy, ii, fCarryOver))
						break
					# Accumulate rainfall.
					drainageMap[ii] += fCarryOver + avrRain[ii]
					fCarryOver = drainageMap[ii]
					if iLength:
						iLength += 1
					elif drainageMap[ii] >= fRiverThreshold:
						if noMoreFlow[ii] == 2:
							drainageMap[idxPrev] = fRiverThreshold
						iLength += 1
					# Update flow.
					flow1, flow2 = flowMap[ii]
					if flow2 != -1:
						if iLength and fCarryOver < 2 * fRiverThreshold:
							iTemp1 = 0
							iTemp2 = fCarryOver - fRiverThreshold
							fCarryOver = fRiverThreshold
						else:
							iTemp1 = iLength
							fCarryOver /= 2
							iTemp2 = fCarryOver
						queueList.append((xx, yy, ii, flow2, iTemp1, iTemp2))

					if flow1 == -1:
						if noMoreFlow[ii] == 1 and iLength == 1 and drainageMap[idxPrev] < fRiverThreshold:
							drainageMap[idxPrev] = fRiverThreshold
						elif noMoreFlow[ii] == -1 and iLength == 1 and drainageMap[idxPrev] < fRiverThreshold:
							drainageMap[i] = 0
						if queueList:
							xx, yy, ii, flow1, iLength, fCarryOver = queueList.pop()
						else:
							break
					idxPrev = ii
				else:
					print "Drainage logical error 2 - bug"
					break
		queueList = []
		while aList:
			x, y, i, drainage = aList.pop()
			# print "	Generating River Map Debug Point 3"
			while True:
				drainageMap[i] += drainage
				flow1, flow2 = flowMap[i]
				if flow1 == -1:
					break
				if flow2 != -1:
					xx, yy = x, y
				if flow1 == N:
					y += 1
				elif flow1 == S:
					y -= 1
				elif flow1 == W:
					x -= 1
				elif flow1 == E:
					x += 1
				i = GetIndex(x, y)
				if flow2 != -1 and drainageMap[i] >= fRiverThreshold:
					if flow2 == N:
						y = yy + 1
					elif flow2 == S:
						y = yy - 1
					elif flow2 == W:
						x = xx - 1
					elif flow2 == E:
						x = xx + 1
					i = GetIndex(x, y)
		i = -1
		for y in xrange(iHeight):
			for x in xrange(iWidth):
				i += 1
				if drainageMap[i] >= fRiverThreshold:
					if flowMap[i][1] == -1:
						self.riverMap[i] = flowMap[i]
					else:
						bFlow0 = False
						bFlow1 = False
						xx, yy = GetNeighbor(x, y, flowMap[i][0])
						ii = GetIndex(xx, yy)
						if drainageMap[ii] >= fRiverThreshold:
							bFlow0 = True
						xx, yy = GetNeighbor(x, y, flowMap[i][1])
						ii = GetIndex(xx, yy)
						if drainageMap[ii] >= fRiverThreshold:
							bFlow1 = True
						if bFlow0 and bFlow1:
							self.riverMap[i] = flowMap[i]
						elif bFlow0:
							self.riverMap[i] = flowMap[i][0], -1
						elif bFlow1:
							self.riverMap[i] = flowMap[i][1], -1
						else:
							print "River placement bug, this shouldn't really happen."
							self.riverMap[i] = -1, -1
				else:
					self.riverMap[i] = -1, -1

rm = None


class BonusPlacer:
	def __init__(self):
		return


	def AddBonuses(self):
		print "Adding Bonuses"
		GC = CyGlobalContext()
		MAP = GC.getMap()
		MAP.recalculateAreas()
		iWorldSize = mc.iWorldSize
		# TODO: Adjust min bonuses by map size, iOrder value (strategics vs not). worldSize is 1-7 in value, use int(size/3)+1 or smth?
		fBonusMult = mc.fBonusMult
		self.aBonusList = bonusList = []
		# Create and shuffle the bonus list.
		n = 0
		pOrderDict = {}
		iNumBonusInfos = GC.getNumBonusInfos()
		self.bonusDict = array('H', [0] * iNumBonusInfos)
		plotIndexList = range(mc.iArea)
		for iBonus in xrange(iNumBonusInfos):
			CvBonusInfo = GC.getBonusInfo(iBonus)
			iPlaceOrder = CvBonusInfo.getPlacementOrder()
			# Filter out bonuses with iPlacementOrder at -1 or below.
			if iPlaceOrder < 1:
				n += 1
				continue
			bonus = BonusArea()
			bonus.indeXML = iBonus
			# Calculate desired amount
			fBaseCount = (
				(
					CvBonusInfo.getConstAppearance() +
					randint(0, CvBonusInfo.getRandAppearance1()) +
					randint(0, CvBonusInfo.getRandAppearance2()) +
					randint(0, CvBonusInfo.getRandAppearance3()) +
					randint(0, CvBonusInfo.getRandAppearance4())
				) / 100.0
			)
			iTilesPer = CvBonusInfo.getTilesPer()
			fDensityCount = 0
			if iTilesPer > 0:
				iNumPossible = 0
				for i in plotIndexList:
					plot = MAP.plotByIndex(i)
					if self.PlotCanHaveBonus(plot, iBonus, True, False):
						iNumPossible += 1
				fDensityCount = 10.0 * iNumPossible / (iTilesPer * (iWorldSize + 7))
			iBonusCount = int(fBonusMult * (fBaseCount + fDensityCount))
			if iBonusCount < 1:
				iBonusCount = 1
			print "%s - Base Count = %.2f - Density Count = %.2f - Multiplier: %.2f\n\tDesired amount = %d" % (CvBonusInfo.getType(), fBaseCount, fDensityCount, fBonusMult, iBonusCount)
			bonus.desiredBonusCount = iBonusCount

			bonusList.append(bonus)
			# Check which placement orders are used.
			if iPlaceOrder in pOrderDict:
				pOrderDict[iPlaceOrder].append(iBonus)
			else:
				pOrderDict[iPlaceOrder] = [iBonus]

		shuffle(bonusList)
		self.iNumBonuses = iNumBonuses = iNumBonusInfos - n
		self.AssignBonusAreas(iNumBonuses, bonusList)
		bonusDictLoc = self.bonusDict
		# Shuffle the list of map indices.
		shuffle(plotIndexList)
		startAtIndex = 0

		pOrderList = sorted(pOrderDict.items())
		for iOrder, aList in pOrderList:
			placementList = []
			for indeXML in aList:
				for n in xrange(bonusList[bonusDictLoc[indeXML]].desiredBonusCount):
					placementList.append(indeXML)
			if len(placementList) > 0:
				shuffle(placementList)
				for indeXML in placementList:
					startAtIndex = self.AddBonusType(indeXML, plotIndexList, startAtIndex, iWorldSize)
		# Now check to see that all resources have been placed at least once while ignoring area rules.
		for i in xrange(iNumBonuses):
			bonus = bonusList[i]
			if bonus.currentBonusCount == 0 and bonus.desiredBonusCount > 0:
				startAtIndex = self.AddEmergencyBonus(bonus, False, plotIndexList, startAtIndex)
		#now check again to see that all resources have been placed at least once,
		#this time ignoring area rules and also class spacing
		for i in xrange(iNumBonuses):
			bonus = bonusList[i]
			if bonus.currentBonusCount == 0 and bonus.desiredBonusCount > 0:
				startAtIndex = self.AddEmergencyBonus(bonus, True, plotIndexList, startAtIndex)
		#now report resources that simply could not be placed
		for iOrder, aList in pOrderList:
			for indeXML in aList:
				CvBonusInfo = GC.getBonusInfo(indeXML)
				bonus = bonusList[bonusDictLoc[indeXML]]
				print "%d - Placed %d, desired %d for %s" %(CvBonusInfo.getPlacementOrder(), bonus.currentBonusCount, bonus.desiredBonusCount, CvBonusInfo.getType())


	# AIAndy - Changed to start at the end of the last run in the plot list.
	def AddBonusType(self, indeXML, plotIndexList, startAtIndex, iWorldSize):
		# First get bonus/area link.
		bonus = self.aBonusList[self.bonusDict[indeXML]]
		iDesired = bonus.desiredBonusCount
		if bonus.currentBonusCount >= iDesired:
			return False
		GC = CyGlobalContext()
		MAP = GC.getMap()
		GAME = GC.getGame()
		bonusInfo = GC.getBonusInfo(indeXML)
		plotListLength = len(plotIndexList)
		lastI = 0
		# Now, add bonuses.
		for i in xrange(startAtIndex, startAtIndex + plotListLength):
			index = 0
			lastI = i
			if i >= plotListLength:
				index = plotIndexList[i - plotListLength]
			else: index = plotIndexList[i]

			CyPlot = MAP.plotByIndex(index)
			if not self.CanPlaceBonus(CyPlot, indeXML, False):
				continue
			# Place bonus
			CyPlot.setBonusType(indeXML)
			bonus.currentBonusCount += 1
			# Clustering
			iGroupRange = bonusInfo.getGroupRange()
			if iGroupRange < 1: break
			iRand = bonusInfo.getGroupRand()
			if iRand < 1: break
			# Scale by worldsize
			if iWorldSize / 3 > 0:
				iGroupRange += iWorldSize / 3 # increase range
				iRand -= iRand * iGroupRange / (iGroupRange + 4) # decrease chance

			if iRand < 1: iRand = 1
			iMaxCluster = iGroupRange + (iWorldSize + 1) / 2
			iDeficit = iDesired - bonus.currentBonusCount
			if iMaxCluster > iDeficit:
				iMaxCluster = iDeficit
			iCluster = 0
			x = CyPlot.getX()
			y = CyPlot.getY()
			for dx in xrange(-iGroupRange, iGroupRange + 1):
				for dy in xrange(-iGroupRange, iGroupRange + 1):
					CyPlotX = self.plotXY(x, y, dx, dy)
					if CyPlotX and GAME.getSorenRandNum(100, "0-99") < iRand and self.PlotCanHaveBonus(CyPlotX, indeXML, False):
						#place bonus
						CyPlotX.setBonusType(indeXML)
						bonus.currentBonusCount += 1
						iCluster += 1
						if iCluster == iMaxCluster:
							print ("Group Placed %d " % iCluster) + bonusInfo.getType()
							return (lastI + 1) % plotListLength
			if iCluster:
				print ("Group Placed %d " % iCluster) + bonusInfo.getType()
			break
		return (lastI + 1) % plotListLength


	#AIAndy - Changed to start at the end of the last run in the plot list and not shuffle an extra plot list
	def AddEmergencyBonus(self, bonus, ignoreClass, plotIndexList, startAtIndex):
		GC = CyGlobalContext()
		MAP = GC.getMap()
		bonusInfo = GC.getBonusInfo(bonus.indeXML)
		plotListLength = len(plotIndexList)
		lastI = 0
		featureForest = GC.getInfoTypeForString("FEATURE_FOREST")
		for i in xrange(startAtIndex, startAtIndex + plotListLength):
			index = 0
			lastI = i
			if i >= plotListLength:
				index = plotIndexList[i - plotListLength]
			else:
				index = plotIndexList[i]
			plot = MAP.plotByIndex(index)

			if ignoreClass and self.PlotCanHaveBonus(plot, bonus.indeXML, True) or self.CanPlaceBonus(plot, bonus.indeXML, True):
				#temporarily remove any feature
				featureEnum = plot.getFeatureType()
				if featureEnum == featureForest:
					featureVariety = plot.getFeatureVariety()
					plot.setFeatureType(FeatureTypes.NO_FEATURE, -1)
				#place bonus
				plot.setBonusType(bonus.indeXML)
				bonus.currentBonusCount += 1
				#restore the feature if possible
				if featureEnum == featureForest:
					if bonusInfo == None or bonusInfo.isFeature(featureEnum):
						plot.setFeatureType(featureEnum, featureVariety)
				print "Emergency placement of 1 %(bt)s" % {"bt":bonusInfo.getType()}
				break
		lastI = (lastI + 1) % plotListLength
		return lastI


	def plotXY(self, x, y, dx, dy):
		# The one that civ uses will return junk so I have to make one that will not.
		x = (x + dx) % mc.iWidth
		y = y + dy
		if y < 0 or y > mc.iHeight - 1:
			return None
		return CyMap().plot(x, y)


	def AssignBonusAreas(self, numBonuses, bonusListLoc):
		GC = CyGlobalContext()
		MAP = GC.getMap()
		# Build area list
		self.areas = areas = []
		for i in xrange(MAP.getIndexAfterLastArea()):
			area = MAP.getArea(i)
			if not area.isNone():
				areas.append(area)

		bonusDictLoc = self.bonusDict
		for i in xrange(numBonuses):
			indeXML = bonusListLoc[i].indeXML
			bonusDictLoc[indeXML] = i
			bonusInfo = GC.getBonusInfo(indeXML)
			if not bonusInfo.isOneArea():
				continue # Only assign areas to area bonuses.
			areaSuitabilityList = []
			minAreaSize = bonusInfo.getMinAreaSize()
			for area in self.areas:
				if area.getNumTiles() >= minAreaSize:
					aS = AreaSuitability(area.getID())
					aS.suitability, aS.numPossible = self.CalculateAreaSuitability(area, indeXML)
					areaSuitabilityList.append(aS)
			# Calculate how many areas to assign.
			areasPerBonus = 1
			#Sort areaSuitabilityList best first
			areaSuitabilityList.sort(lambda a, b:cmp(b.numPossible, a.numPossible))
			#assign the best areas to this bonus
			for n in xrange(areasPerBonus):
				self.aBonusList[i].areaList.append(areaSuitabilityList[n].areaID)
			#assign areas that have a high suitability also
			for n in xrange(areasPerBonus,len(areaSuitabilityList)):
				if areaSuitabilityList[n].suitability > 0.3:
					self.aBonusList[i].areaList.append(areaSuitabilityList[n].areaID)
		self.bonusDict = bonusDictLoc


	def CanPlaceBonus(self, CyPlot, indeXML, bIgnoreArea):
		if not self.PlotCanHaveBonus(CyPlot, indeXML, bIgnoreArea):
			return False
		GC = CyGlobalContext()
		x = CyPlot.getX()
		y = CyPlot.getY()
		areaID = CyPlot.getArea()
		bonusInfo = GC.getBonusInfo(indeXML)
		''' Rewrite to something that actually makes sense.
		if CyPlot.isWater():
			MAP = GC.getMap()
			if 100 * MAP.getNumBonusesOnLand(indeXML) / (MAP.getNumBonuses(indeXML) + 1) < bonusInfo.getMinLandPercent():
				return False
		'''
		#Make sure there are no bonuses of the same class (but a different type) nearby:
		iBonusClass = bonusInfo.getBonusClassType()
		classInfo = GC.getBonusClassInfo(iBonusClass)
		iRange0 = 0
		if classInfo:
			iRange0 = classInfo.getUniqueRange()
			if iRange0 > 0:
				iRange0 += (mc.iWorldSize + 1) / 2
				for dx in xrange(-iRange0, iRange0 + 1):
					for dy in xrange(-iRange0, iRange0 + 1):
						if dx or dy:
							CyPlotX = self.plotXY(x, y, dx, dy)
							if CyPlotX and areaID == CyPlotX.getArea():
								eOtherBonus = CyPlotX.getBonusType(TeamTypes.NO_TEAM)
								if eOtherBonus > -1 and GC.getBonusInfo(eOtherBonus).getBonusClassType() == iBonusClass:
									return False
			elif iRange0 < 0:
				iRange0 = 0
		#Make sure there are no bonuses of the same type nearby:
		iRange1 = bonusInfo.getUniqueRange()
		if iRange1 > 0:
			iRange1 += mc.iWorldSize
			if iRange1 > iRange0:
				for dx in xrange(-iRange1, iRange1 + 1):
					for dy in xrange(-iRange1, iRange1 + 1):
						if dx >= -iRange0 and dx <= iRange0 and dy >= -iRange0 and dy <= iRange0: continue
						CyPlotX = self.plotXY(x, y, dx, dy)
						if CyPlotX and areaID == CyPlotX.getArea() and CyPlotX.getBonusType(TeamTypes.NO_TEAM) == indeXML:
							return False
		return True


	def PlotCanHaveBonus(self, plot, indeXML, bIgnoreArea, bFree = True):
		#This function is like CvPlot::canHaveBonus but will ignore blocking features and checks for a valid area.
		if bFree and plot.getBonusType(TeamTypes.NO_TEAM) != BonusTypes.NO_BONUS:
			return False
		GC = CyGlobalContext()
		bonusInfo = GC.getBonusInfo(indeXML)

		iTemp = plot.getLatitude()
		if iTemp > bonusInfo.getMaxLatitude() or iTemp < bonusInfo.getMinLatitude():
			return False

		if plot.isPeak():
			if not bonusInfo.isPeaks():
				return False
		else:
			if plot.isHills():
				if not bonusInfo.isHills():
					return False
			elif plot.isFlatlands():
				if not bonusInfo.isFlatlands():
					return False

			iTerrain = plot.getTerrainType()
			iFeature = plot.getFeatureType()
			if bonusInfo.isTerrain(iTerrain):
				ICE = GC.getInfoTypeForString("FEATURE_ICE")
				if iFeature == ICE and not bonusInfo.isFeature(ICE):
					# Special case, ice block bonuses, mostly because it looks graphically glitchy.
					return False
			elif iFeature == -1 or not bonusInfo.isFeature(iFeature) or not bonusInfo.isFeatureTerrain(iTerrain):
				return False

		if bonusInfo.isBonusCoastalOnly() and not plot.isCoastal():
			return False

		if bonusInfo.isNoRiverSide() and plot.isRiverSide():
			return False

		iTemp = bonusInfo.getMinAreaSize()
		if iTemp > 0:
			iTemp + 2*mc.iWorldSize
			if iTemp > 1 and plot.area().getNumTiles() < iTemp:
				return False

		if not bIgnoreArea and bonusInfo.isOneArea():
			if plot.getArea() not in self.aBonusList[self.bonusDict[indeXML]].areaList:
				return False

		if not plot.isPotentialCityWork():
			return False

		return True


	def GetUniqueBonusTypeCountInArea(self, area):
		GC = CyGlobalContext()
		areaID = area.getID()
		uniqueBonusCount = 0
		for bonus in self.aBonusList:

			if not GC.getBonusInfo(bonus.indeXML).isOneArea():
				continue
			if areaID in bonus.areaList:
				uniqueBonusCount += 1
		return uniqueBonusCount


	def GetSameClassTypeCountInArea(self, area, indeXML):
		GC = CyGlobalContext()
		areaID = area.getID()
		uniqueBonusCount = 0
		bonusInfo = GC.getBonusInfo(indeXML)
		eClass = bonusInfo.getBonusClassType()
		if eClass == BonusClassTypes.NO_BONUSCLASS:
			return 0
		classInfo = GC.getBonusClassInfo(eClass)
		if classInfo == None:
			return 0
		iRange = classInfo.getUniqueRange()
		if iRange < 1:
			return 0
		for bonus in self.aBonusList:
			bonusInfo = GC.getBonusInfo(bonus.indeXML)
			if not bonusInfo.isOneArea():
				continue
			if bonusInfo.getBonusClassType() != eClass:
				continue
			if areaID in bonus.areaList:
				uniqueBonusCount += 1
				break
		# Same class types tend to really crowd out any bonus types that are placed later.
		# A single cow can block 5 * 5 squares of pig territory for example.
		# Probably shouldn't place them on the same area at all, but sometimes it might be necessary.
		return uniqueBonusCount * iRange * iRange


	def CalculateAreaSuitability(self, area, indeXML):
		MAP = CyGlobalContext().getMap()
		uniqueTypesInArea	= self.GetUniqueBonusTypeCountInArea(area)
		sameClassTypesInArea = self.GetSameClassTypeCountInArea(area, indeXML)
		#Get the raw number of suitable tiles
		areaID = area.getID()
		iPossible = 0
		for i in xrange(mc.iArea):
			plot = MAP.plotByIndex(i)
			if plot.getArea() == areaID and self.PlotCanHaveBonus(plot, indeXML, True):
				iPossible += 1

		iPossible /= uniqueTypesInArea + sameClassTypesInArea + 1
		suitability = 1.0*iPossible / area.getNumTiles()
		return suitability, iPossible

bp = BonusPlacer()


class BonusArea:
	def __init__(self):
		self.indeXML = -1
		self.desiredBonusCount = -1
		self.currentBonusCount = 0
		self.areaList = []


class AreaSuitability:
	def __init__(self, areaID):
		self.areaID = areaID
		self.suitability = 0
		self.numPossible = 0


class StartingPlotFinder:
	def __init__(self):
		return

	def SetStartingPlots(self):
		GC = CyGlobalContext()
		MAP = GC.getMap()
		MAP.recalculateAreas()
		# Cache Plot Value
		self.plotvalueList = []
		self.plotfoodList = []
		for y in xrange(mc.iHeight):
			for x in xrange(mc.iWidth):
				plot = MAP.plot(x, y)
				# Base Yield
				commerce	= plot.calculateBestNatureYield(YieldTypes.YIELD_COMMERCE,	 TeamTypes.NO_TEAM)
				food		= plot.calculateBestNatureYield(YieldTypes.YIELD_FOOD,		 TeamTypes.NO_TEAM)
				production	= plot.calculateBestNatureYield(YieldTypes.YIELD_PRODUCTION, TeamTypes.NO_TEAM)
				# Bonus Yield
				bonusEnum = plot.getBonusType(TeamTypes.NO_TEAM)
				value = 0
				if bonusEnum != BonusTypes.NO_BONUS:
					value += 3
					bonusInfo = GC.getBonusInfo(bonusEnum)
					if bonusInfo.getTechReveal() == TechTypes.NO_TECH or GC.getTechInfo(bonusInfo.getTechReveal()).getEra() < GC.getGame().getStartEra() + 2:
						commerce	+= bonusInfo.getYieldChange(YieldTypes.YIELD_COMMERCE)
						food		+= bonusInfo.getYieldChange(YieldTypes.YIELD_FOOD)
						production	+= bonusInfo.getYieldChange(YieldTypes.YIELD_PRODUCTION)
				value += commerce + food + production
				self.plotvalueList.append(value)
				self.plotfoodList.append(food)
		# A shuffled player list.
		player_list = []
		iNumPlayers = 0
		for i in xrange(GC.getMAX_PC_PLAYERS()):
			if GC.getPlayer(i).isEverAlive():
				player_list.append(i)
				iNumPlayers += 1
		shuffle(player_list)
		print "Number of players: %d" % iNumPlayers
		# Build area list
		areas = []
		for i in xrange(MAP.getIndexAfterLastArea()):
			area = MAP.getArea(i)
			if not area.isNone():
				areas.append(area)
		# old/new world status
		# Get official areas and make corresponding lists that determines
		# old world vs. new world and also the pre-settled value.
		iArea = mc.iArea
		bNewWorld = mc.bNewWorld
		iNW = iOW = 0
		areaOldWorld = []
		for i in xrange(len(areas)):
			for pI in xrange(iArea):
				plot = MAP.plotByIndex(pI)
				if plot.getArea() == areas[i].getID():
					if bNewWorld and coMa.areaMap.areaID[pI] == coMa.newWorldID:
						areaOldWorld.append(False)
						iNW += 1
					else:
						areaOldWorld.append(True)
						iOW += 1
					break
		print "World areas: %d" % len(areaOldWorld)
		if bNewWorld:
			print "	Old world: %d" % iOW
			print "	New world: %d" % iNW
		#LM - Set up a map that merges Coast-linked landmasses so we can allow island starts while still ensuring adequate expansion room.
		regionMap = AreaMap()
		regionMap.defineAreas(em.isDeepWaterMatch)
		startingAreaList = []
		iWorldSize = mc.iWorldSize + 1
		iPangea = mc.bPangea * 9 + 1
		fMinIslandSize = mc.fLandPercent * iPangea * iWorldSize * 6 / (bNewWorld + 1)
		print "Min. Island Size: %f" % fMinIslandSize
		fMinRegionSize = fMinIslandSize * 12
		print "Min. Region Size: %f" % fMinRegionSize
		iStartingAreas = 0
		for i in xrange(len(areas)):
			if areaOldWorld[i] and areas[i].getNumTiles() >= fMinIslandSize:
				iRegionSize = 0
				for pI in xrange(iArea):
					plot = MAP.plotByIndex(pI)
					if plot.getArea() == areas[i].getID():
						iRegionSize = regionMap.getAreaByID(regionMap.areaID[pI]).size
						print "Region Size for area %d: %d" % (regionMap.areaID[pI], iRegionSize)
						break
				if iRegionSize >= fMinRegionSize:
					startArea = StartingArea(areas[i].getID())
					startingAreaList.append(startArea)
					iStartingAreas += 1
		# We are assuming there is now at least 1 starting area, else something has gone terribly wrong.
		# Get the value of the whole old world
		fOldWorldValue = 0.0
		for i in xrange(iStartingAreas):
			fOldWorldValue += startingAreaList[i].fRawValue
		# Calulate value per player of old world
		fOldWorldValuePerPlayer = fOldWorldValue / (iNumPlayers + 1)
		# Sort startingAreaList by rawValue
		startingAreaList.sort(lambda x, y: cmp(x.fRawValue, y.fRawValue))
		# Get rid of areas that have less value than fOldWorldValuePerPlayer as they are too small to put a player on.
		iAreas = 0
		iDiv = 0
		while iAreas < 1:
			iDiv += 2
			iAreas = iStartingAreas - iNumPlayers / iDiv
		for i in xrange(iAreas):
			if startingAreaList[0].fRawValue < fOldWorldValuePerPlayer:
				del startingAreaList[0]
				iStartingAreas -= 1
			else: break #All remaining should be big enough

		# Recalculate the value of the whole old world
		fOldWorldValue = 0.0
		for i in xrange(iStartingAreas):
			fOldWorldValue += startingAreaList[i].fRawValue
		# Recalulate value per player of old world so we are starting more accurately
		fOldWorldValuePerPlayer = fOldWorldValue / iNumPlayers
		# Record the ideal number of players for each continent
		for startingArea in startingAreaList:
			# Store fractional values for accurate scaling below.
			startingArea.idealNumberOfPlayers = startingArea.fRawValue / fOldWorldValuePerPlayer
		# Now we want best first
		startingAreaList.reverse()
		print "[INFO] There are %d starting areas." % iStartingAreas

		fIdeal = 0.0
		for startingArea in startingAreaList:
			fIdeal += startingArea.idealNumberOfPlayers

		fRatio = iNumPlayers / fIdeal
		if fRatio != 1.0:
			for startingArea in startingAreaList:
				startingArea.idealNumberOfPlayers *= fRatio

		# Reallocate players as needed to fix any overloaded landmasses.
		while iStartingAreas > 0:
			for startingArea in startingAreaList:
				fPlots = 1.0*len(startingArea.plotList)
				fDiff = startingArea.idealNumberOfPlayers - fPlots
				if fDiff > 0.0:
					fSearchTotal = 0.0
					for searchArea in startingAreaList:
						fTemp = searchArea.idealNumberOfPlayers
						if fTemp < len(searchArea.plotList):
							fSearchTotal += fTemp
					if fSearchTotal > 0.0:
						startingArea.idealNumberOfPlayers = fPlots
						fRatio = (fSearchTotal + fDiff) / fSearchTotal
						for searchArea in startingAreaList:
							if searchArea.idealNumberOfPlayers < len(searchArea.plotList):
								searchArea.idealNumberOfPlayers *= fRatio
					else:
						raise ValueError, "Not enough room on the map to place all players!"
						iStartingAreas = 0
						break
			else: iStartingAreas -= 1

		# Done with fractional values.
		for startingArea in startingAreaList:
			startingArea.idealNumberOfPlayers = int(round(startingArea.idealNumberOfPlayers))
		# Total player allocation should be pretty close to the correct number here. Smooth out any difference that's left.
		idealTotal = 0
		for startingArea in startingAreaList:
			idealTotal += startingArea.idealNumberOfPlayers
		if idealTotal < iNumPlayers:
			iNum = iNumPlayers - idealTotal
			while iNum > 0:
				iEntry = iNum
				for startingArea in startingAreaList:
					if startingArea.idealNumberOfPlayers < len(startingArea.plotList):
						startingArea.idealNumberOfPlayers += 1
						iNum -= 1
						if iNum == 0:
							break
				if iNum == iEntry:
					raise ValueError, "Not enough room on the map to place all players!"
					break
		elif idealTotal > iNumPlayers:
			iNum = idealTotal - iNumPlayers
			while iNum > 0:
				iEntry = iNum
				for startingArea in startingAreaList:
					if startingArea.idealNumberOfPlayers > 0:
						startingArea.idealNumberOfPlayers -= 1
						iNum -= 1
						if iNum == 0:
							break
				if iNum == iEntry:
					raise ValueError, "Not enough room on the map to place all players!"
					break
		#Assign players.
		iCount = 0
		for startingArea in startingAreaList:
			for i in xrange(startingArea.idealNumberOfPlayers):
				startingArea.playerList.append(player_list[iCount])
				iCount += 1
			startingArea.FindStartingPlots()
		if iNumPlayers > iCount:
			raise ValueError, "Some players not placed in starting plot finder!"
		#Now set up for normalization
		self.plotList = []
		for startingArea in startingAreaList:
			self.plotList.extend(startingArea.plotList)
		#find the best totalValue
		self.plotList.sort(lambda a, b:cmp(b.fTotalValue, a.fTotalValue))
		bestTotalValue = self.plotList[0].fTotalValue
		for i in xrange(len(self.plotList)):
			if not self.plotList[i].vacant:
				currentTotalValue = self.plotList[i].fTotalValue
				percentLacking = 1.0 - currentTotalValue / bestTotalValue
				if percentLacking > .0 and mc.fBonusMult:
					value1 = int(percentLacking / 0.2)
					if 5 > value1:
						bonuses = value1
					else:
						bonuses = 5
					self.boostCityPlotValue(self.plotList[i].x, self.plotList[i].y, bonuses, self.plotList[i].isCoast())


	def getCityPotentialValue(self, x, y):
		GC = CyGlobalContext()
		start = GC.getMap().plot(x, y)
		# Block invalid locations!
		if start.isWater() or start.isImpassable():
			return -1, -1
		if mc.fMaxStartLat < start.getLatitude():
			return -1, -1
		terrainInfo = GC.getTerrainInfo(start.getTerrainType())
		if not terrainInfo.isFound():
			return -1, -1
		featureEnum = start.getFeatureType()
		if featureEnum != FeatureTypes.NO_FEATURE:
			featureInfo = GC.getFeatureInfo(featureEnum)
			if featureInfo.isNoCity():
				return -1, -1
		#The StartPlot class has a nifty function to determine salt water vs. fresh
		totalFood  = 0
		cityPlotList = []
		sPlot = StartPlot(x, y, 0.0)
		for n in xrange(21):
			plot = plotCity(x, y, n)
			i = GetIndex(plot.getX(), plot.getY())
			totalFood += spf.plotfoodList[i]
			value = spf.plotvalueList[i]
			cityPlotList.append(value)
		usablePlots = int(round(totalFood / float(GC.getFOOD_CONSUMPTION_PER_POPULATION())))
		cityPlotList.sort(lambda a, b:cmp(b, a))
		#value is obviously limited to available food
		fValue = 0.0
		if usablePlots > 21:
			usablePlots = 21
		for n in xrange(usablePlots):
			fValue += cityPlotList[n]
		if sPlot.isCoast():
			fValue *= mc.CoastalCityValueBonus
		#LM - Use isRiver, not isRiverSide!
		if start.isRiver():
			fValue *= mc.RiverCityValueBonus
		#LM - Add small bonus for hill defense.
		if start.isHills():
			fValue *= mc.HillCityValueBonus
		return totalFood, fValue


	def boostCityPlotValue(self, x, y, bonuses, bCoastalCity):
		GC = CyGlobalContext()
		iFoodPerPop = GC.getFOOD_CONSUMPTION_PER_POPULATION()
		iAreaID = GC.getMap().plot(x, y).getArea()
		startEra = GC.getGame().getStartEra() + 1
		#Shuffle the bonus order so that different cities have different preferences for bonuses
		iNumBonuses = bp.iNumBonuses
		bonusList = range(iNumBonuses)
		shuffle(bonusList)
		#Do this process in 3 passes for each yield type
		yields = []
		yields.append(YieldTypes.YIELD_PRODUCTION)
		yields.append(YieldTypes.YIELD_COMMERCE)
		yields.append(YieldTypes.YIELD_FOOD)
		plotList = []
		for i in xrange(1, 21):
			plotList.append(plotCity(x, y, i))
		shuffle(plotList)
		bonusCount = 0
		for n in xrange(3 * bonuses + 1):
			for CyPlot in plotList:
				if bonusCount >= bonuses:
					return
				if CyPlot.isWater():
					if not bCoastalCity: continue
				elif iAreaID != CyPlot.getArea(): continue

				if CyPlot.getBonusType(TeamTypes.NO_TEAM) != BonusTypes.NO_BONUS:
					continue
				# switch to food if food is needed
				food, value = self.getCityPotentialValue(x, y)
				usablePlots = food / iFoodPerPop
				if usablePlots < 9:
					iYieldType = YieldTypes.YIELD_FOOD
				else:
					iYieldType = yields[(n + bonusCount) % 3]
				# temporarily remove any feature
				featureEnum = CyPlot.getFeatureType()
				if featureEnum != FeatureTypes.NO_FEATURE:
					featureVariety = CyPlot.getFeatureVariety()
					CyPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)
				for b in xrange(iNumBonuses):
					bonusEnum = bonusList[b]
					indeXML = bp.aBonusList[bonusEnum].indeXML
					CvBonusInfo = GC.getBonusInfo(indeXML)
					if CvBonusInfo.getYieldChange(iYieldType) < 1:
						continue
					iTech = CvBonusInfo.getTechReveal()
					if iTech != -1 and GC.getTechInfo(iTech).getEra() > startEra:
						continue
					if not bp.PlotCanHaveBonus(CyPlot, bonusEnum, False) and not bp.PlotCanHaveBonus(CyPlot, bonusEnum, True):
						continue
					CyPlot.setBonusType(bonusEnum)
					bonusCount += 1
					break
				#restore the feature if possible
				if featureEnum != FeatureTypes.NO_FEATURE:
					CvBonusInfo = GC.getBonusInfo(CyPlot.getBonusType(TeamTypes.NO_TEAM))
					if not CvBonusInfo or CvBonusInfo.isFeature(featureEnum):
						CyPlot.setFeatureType(featureEnum, featureVariety)

spf = StartingPlotFinder()

class StartingArea:
	def __init__(self, areaID):
		self.areaID = areaID
		self.plotList   = []
		self.playerList = []
		self.distanceTable = array('i')
		self.fRawValue = 0.0
		self.CalculatePlotList()
		self.idealNumberOfPlayers = 0


	def CalculatePlotList(self):
		MAP = CyMap()
		for y in xrange(mc.iHeight):
			for x in xrange(mc.iWidth):
				plot = MAP.plot(x, y)
				if plot.getArea() == self.areaID:
					food, value = spf.getCityPotentialValue(x, y)
					#LM - Invalid locations are given a value of -1, which is blocked. Highly undesirable but technically valid locations are given a value of 0
					#which is also blocked, with any landmass overflows now handled above. I've left the values separate anyway though, in case they're ever used.
					if value > 0.0:
						startPlot = StartPlot(x, y, value)
						self.plotList.append(startPlot)
		#Sort plots by declining local value.
		self.plotList.sort(lambda a, b: cmp(b.fLocalValue, a.fLocalValue))
		# Eliminate some plots by having the best plot eat plots within 2 squares, then same for next, etc.
		numPlots = len(self.plotList)
		dl = (mc.iWorldSize + 3) / 3
		for n in xrange(numPlots):
			#At some point the length of plot list will be much shorter than at
			#the beginning of the loop, so it can never end normally
			if n + 1 >= len(self.plotList):
				break
			x = self.plotList[n].x
			y = self.plotList[n].y
			for yy in xrange(y - dl, y + dl + 1):
				for xx in xrange(x - dl, x + dl + 1):
					if xx == x and yy == y:
						continue
					i = GetIndex(xx, yy)
					if i == -1:
						continue
					xx = xx % mc.iWidth #wrap xx
					yy = yy % mc.iHeight #wrap yy
					for m in xrange(n + 1, len(self.plotList)):
						if self.plotList[m].x == xx and self.plotList[m].y == yy:
							del self.plotList[m]
							break
		print "	Potential starting plots in areaID = %(a)d is %(p)d" % {"a":self.areaID, "p":len(self.plotList)}
		# At this point we should have a list of the very best places to build cities on this continent.
		# Now we need a table with the distance from each city to every other city.
		iLength = len(self.plotList)
		self.distanceTable = [-1] * iLength * iLength
		#Fill distance table
		for n in xrange(iLength):
			#While we're already looping lets calculate the raw value
			self.fRawValue += self.plotList[n].fLocalValue
			avgDistance = 0
			for m in xrange(n, iLength):
				nPlot = MAP.plot(self.plotList[n].x, self.plotList[n].y)
				mPlot = MAP.plot(self.plotList[m].x, self.plotList[m].y)
				MAP.resetPathDistance()
				distance = MAP.calculatePathDistance(nPlot, mPlot)
				#If path fails try reversing it
				self.distanceTable[n * iLength + m] = distance
				self.distanceTable[m * iLength + n] = distance
				avgDistance += distance
			self.plotList[n].avgDistance = avgDistance


	def FindStartingPlots(self):
		GC = CyGlobalContext()
		numPlayers = len(self.playerList)
		if numPlayers <= 0:
			return
		avgDistanceList = []
		for i in xrange(len(self.plotList)):
			avgDistanceList.append(self.plotList[i])
		# Make sure first guy starts on the end and not in the middle,
		# otherwise if there are two players one will start on the middle and the other on the end.
		avgDistanceList.sort(lambda a, b:cmp(b.avgDistance, a.avgDistance))
		#First place players as far as possible away from each other.
		avgDistanceList[0].vacant = False
		for i in xrange(1, numPlayers):
			distanceList = []
			for n in xrange(len(self.plotList)):
				if self.plotList[n].vacant:
					minDistance = -1
					for m in xrange(len(self.plotList)):
						if not self.plotList[m].vacant:
							ii = n * len(self.plotList) + m
							distance = self.distanceTable[ii]
							if distance < minDistance or minDistance == -1:
								minDistance = distance
					self.plotList[n].nearestStart = minDistance
					distanceList.append(self.plotList[n])
			#Find biggest nearestStart and place a start there
			distanceList.sort(lambda a, b:cmp(b.nearestStart, a.nearestStart))
			distanceList[0].vacant = False
		self.CalculateStartingPlotValues()
		#Now place all starting positions
		MAP = GC.getMap()
		n = 0
		for m in xrange(len(self.plotList)):
			if not self.plotList[m].vacant:
				sPlot = MAP.plot(self.plotList[m].x, self.plotList[m].y)
				if sPlot.isWater():
					raise ValueError, "Start plot is water!"
				sPlot.setImprovementType(-1)
				playerID = self.playerList[n]
				player = GC.getPlayer(playerID)
				sPlot.setStartingPlot(True)
				player.setStartingPlot(sPlot, True)
				n += 1


	def CalculateStartingPlotValues(self):
		numPlots = len(self.plotList)
		for n in xrange(numPlots):
			self.plotList[n].owner = -1
			self.plotList[n].fTotalValue = 0.0
		for n in xrange(numPlots):
			if self.plotList[n].vacant:
				continue
			self.plotList[n].numberOfOwnedCities = 0
			for m in xrange(numPlots):
				i = n * numPlots + m
				nDistance = self.distanceTable[i]
				if nDistance == -1:
					leastDistance = False
				else:
					leastDistance = True #Being optimistic, prove me wrong
				for p in xrange(numPlots):
					if p == n or self.plotList[p].vacant:
						continue
					ii = p * numPlots + m
					pDistance = self.distanceTable[ii]
					if pDistance > -1 and pDistance <= nDistance:
						leastDistance = False #Proven wrong
						break
				if leastDistance:
					self.plotList[n].fTotalValue += self.plotList[m].fLocalValue
					self.plotList[n].numberOfOwnedCities += 1
					self.plotList[m].owner = self.plotList[n]
					self.plotList[m].distanceToOwner = nDistance


class StartPlot:
	def __init__(self, x, y, fLocalValue):
		self.x = x
		self.y = y
		self.fLocalValue = fLocalValue
		self.fTotalValue = 0.0
		self.numberOfOwnedCities = 0
		self.distanceToOwner = -1
		self.nearestStart = -1
		self.vacant = True
		self.owner = None
		self.avgDistance = 0

	def isCoast(self):
		waterArea = CyMap().plot(self.x, self.y).waterArea()
		return not waterArea.isNone() and not waterArea.isLake()

	def isRiverSide(self):
		return CyMap().plot(self.x, self.y).isRiverSide()

	def plot(self):
		return CyMap().plot(self.x, self.y)


##############################################################################
## Map options class
##############################################################################
class MapOptions:
	def __init__(self):
		self.bfirstRun = True
		self.optionList = \
		[	# Title, Default, Random, Choices
			["Hills:",			2,	True, 5],
			["Peaks:",			2,	True, 5],
			["Landform:",		2,	True, 5],
			["World Wrap:",		0, False, 3],
			["Start:",			1, False, 2],
			["Rivers:",			4,	True, 9],
			["Resources:",		3,	True, 7],
			["Pangea Breaker:",	0, False, 2]
		] # When adding/removing options: Update the return of getNumCustomMapOptions().

	def loadMapOptionDefaults(self):
		self.bfirstRun = False
		fileName = os.path.join(self.civFilePath(),"World_MapDefaults.cfg")
		try:
			settings = open(fileName, 'r')
			iDefaultList = pickle.load(settings)
			for i in xrange(len(iDefaultList)):
				self.optionList[i][1] = iDefaultList[i]
			settings.close()
		except IOError:
			print "	Couldn't find ", fileName
		except EOFError:
			print "	Bad contents in ", fileName
		except:
			print "	unexpected problem reading", fileName


	def saveMapOptionDefaults(self):
		fileName = os.path.join(self.civFilePath(),"World_MapDefaults.cfg")
		try:
			settings = open(fileName, 'w')
			iDefault = []
			for iOption in self.optionList:
				iDefault.append(iOption[1])
			print "------\n try to store settings to", fileName
			try:
				pickle.dump(iDefault, settings)
			except Exception, inst:
				print "------\n Pickling Error", inst, "trying to save map settings to", fileName
			settings.close()
			print "	store successful \n------"
		except IOError:
			print "------\n Couldn't create", fileName
		except EOFError:
			print "------\n EOF writing", fileName
		except:
			print "------\n unexpected problem writing", fileName


	def civFilePath(self):
		try:
			folder = os.path.dirname(os.path.realpath(__file__))
			folder = os.path.join(folder[:-6], "Mods\Caveman2Cosmos\UserSettings")
			return folder
		except:
			return ""

	def regRead(self, registry, path, field):
		try:
			pathKey = _winreg.OpenKey(registry, path)
			fieldValue = _winreg.QueryValueEx(pathKey, field)
			return fieldValue[0]
		finally:
			pathKey.Close()

mo = MapOptions()


##############################################################################
## Begin Map-Script
##############################################################################

def getNumCustomMapOptions():
	if mo.bfirstRun:
		print "Preparing World Map Script"
		mo.loadMapOptionDefaults()
	return 8

def getCustomMapOptionDefault(argsList):
	iOption = argsList[0]
	return mo.optionList[iOption][1]

def isAdvancedMap():
	return False

def getCustomMapOptionName(argsList):
	iOption = argsList[0]
	return unicode(mo.optionList[iOption][0])

def getNumCustomMapOptionValues(argsList):
	iOption  = argsList[0]
	return mo.optionList[iOption][3]

def isRandomCustomMapOption(argsList):
	iOption = argsList[0]
	return mo.optionList[iOption][2]

def getCustomMapOptionDescAt(argsList):
	# Register selected options
	optionList = mo.optionList
	if not mo.bfirstRun:
		for i in xrange(len(optionList)):
			iDefault = int(CyGlobalContext().getMap().getCustomMapOption(i))
			optionList[i][1] = iDefault
		mo.optionList = optionList
	# Return names of option alternatives.
	optionID	= argsList[0]
	selectionID = argsList[1]
	# Hills
	if optionID == 0:
		if selectionID == 0:
			return "50%"
		if selectionID == 1:
			return "75%"
		if selectionID == 2:
			return "100%"
		if selectionID == 3:
			return "125%"
		if selectionID == 4:
			return "150%"
	# Peaks
	if optionID == 1:
		if selectionID == 0:
			return "50%"
		if selectionID == 1:
			return "75%"
		if selectionID == 2:
			return "100%"
		if selectionID == 3:
			return "125%"
		if selectionID == 4:
			return "150%"
	# Landform
	if optionID == 2:
		if selectionID == 0:
			return "Dryland"
		if selectionID == 1:
			return "Pangea"
		if selectionID == 2:
			return "Earthlike"
		if selectionID == 3:
			return "Archipelago"
		if selectionID == 4:
			return "Waterworld"
	# World Wrap
	if optionID == 3:
		if selectionID == 0:
			return "Cylindrical"
		if selectionID == 1:
			return "Toroidal"
		if selectionID == 2:
			return "Flat"
	# Start
	if optionID == 4:
		if selectionID == 0:
			return "Everywhere"
		if selectionID == 1:
			if optionList[2][1] == 0 or optionList[2][1] == 1:
				return "Everywhere (Dryland|Pangea)"
			return "Old World"
	# Rivers
	if optionID == 5:
		if selectionID == 0:
			return "-4"
		if selectionID == 1:
			return "-3"
		if selectionID == 2:
			return "-2"
		if selectionID == 3:
			return "-1"
		if selectionID == 4:
			return "0"
		if selectionID == 5:
			return "+1"
		if selectionID == 6:
			return "+2"
		if selectionID == 7:
			return "+3"
		if selectionID == 8:
			return "+4"
	# Resources
	if optionID == 6:
		if selectionID == 0:
			return "None"
		if selectionID == 1:
			return "50%"
		if selectionID == 2:
			return "75%"
		if selectionID == 3:
			return "100%"
		if selectionID == 4:
			return "125%"
		if selectionID == 5:
			return "150%"
		if selectionID == 6:
			return "175%"
	# Pangea Breaker
	if optionID == 7:
		if selectionID == 0: # On
			if optionList[2][1] == 0 or optionList[2][1] == 1:
				return "Off (Dryland|Pangea)"
			return "On"
		if selectionID == 1: # Off
			return "Off"
	return ""


def isClimateMap():
	return True
def isSeaLevelMap():
	return True


def beforeInit():
	optionList = mo.optionList
	print "\n", "Options Selected:"
	# Hills
	if optionList[0][1] == 0:
		print "	%s			50 percent" % optionList[0][0]
	elif optionList[0][1] == 1:
		print "	%s			75 percent" % optionList[0][0]
	elif optionList[0][1] == 2:
		print "	%s			100 percent" % optionList[0][0]
	elif optionList[0][1] == 3:
		print "	%s			125 percent" % optionList[0][0]
	elif optionList[0][1] == 4:
		print "	%s			150 percent" % optionList[0][0]
	# Peaks
	if optionList[1][1] == 0:
		print "	%s			50 percent" % optionList[1][0]
	elif optionList[1][1] == 1:
		print "	%s			75 percent" % optionList[1][0]
	elif optionList[1][1] == 2:
		print "	%s			100 percent" % optionList[1][0]
	elif optionList[1][1] == 3:
		print "	%s			100 percent" % optionList[1][0]
	elif optionList[1][1] == 4:
		print "	%s			150 percent" % optionList[1][0]
	# Landform
	if optionList[2][1] == 0:
		print "	%s		Dryland" % optionList[2][0]
	elif optionList[2][1] == 1:
		print "	%s		Pangea" % optionList[2][0]
	elif optionList[2][1] == 2:
		print "	%s		Earthlike" % optionList[2][0]
	elif optionList[2][1] == 3:
		print "	%s		Archipelago" % optionList[2][0]
	elif optionList[2][1] == 4:
		print "	%s		Waterworld" % optionList[2][0]
	# World Wrap
	if optionList[3][1] == 0:
		print "	%s		Cylindrical" % optionList[3][0]
	elif optionList[3][1] == 1:
		print "	%s		Toroidal" % optionList[3][0]
	elif optionList[3][1] == 2:
		print "	%s		Flat" % optionList[3][0]
	# Start
	if optionList[2][1] == 0 or optionList[2][1] == 1:
		print "	%s			Everywhere (Dryland|Pangea)" % optionList[4][0]
	elif optionList[4][1] == 0:
		print "	%s			Everywhere" % optionList[4][0]
	elif optionList[4][1] == 1:
		print "	%s			Old World" % optionList[4][0]
	# Rivers
	if optionList[5][1] == 0:
		print "	%s			-4" % optionList[5][0]
	elif optionList[5][1] == 1:
		print "	%s			-3" % optionList[5][0]
	elif optionList[5][1] == 2:
		print "	%s			-2" % optionList[5][0]
	elif optionList[5][1] == 3:
		print "	%s			-1" % optionList[5][0]
	elif optionList[5][1] == 4:
		print "	%s			0" % optionList[5][0]
	elif optionList[5][1] == 5:
		print "	%s			+1" % optionList[5][0]
	elif optionList[5][1] == 6:
		print "	%s			+2" % optionList[5][0]
	elif optionList[5][1] == 7:
		print "	%s			+3" % optionList[5][0]
	elif optionList[5][1] == 8:
		print "	%s			+4" % optionList[5][0]
	# Resources
	if optionList[6][1] == 0:
		print "	%s		None" % optionList[6][0]
	elif optionList[6][1] == 1:
		print "	%s		50 percent" % optionList[6][0]
	elif optionList[6][1] == 2:
		print "	%s		75 percent" % optionList[6][0]
	elif optionList[6][1] == 3:
		print "	%s		100 percent" % optionList[6][0]
	elif optionList[6][1] == 4:
		print "	%s		125 percent" % optionList[6][0]
	elif optionList[6][1] == 5:
		print "	%s		150 percent" % optionList[6][0]
	elif optionList[6][1] == 6:
		print "	%s		175 percent" % optionList[6][0]
	# Pangea Breaker
	if optionList[2][1] == 0 or optionList[2][1] == 1:
		print "	%s	Off (Dryland|Pangea)" % optionList[7][0]
	elif optionList[7][1] == 0:
		print "	%s	On" % optionList[7][0]
	elif optionList[7][1] == 1:
		print "	%s	Off" % optionList[7][0]
	# Save new default option values.
	mo.saveMapOptionDefaults()
	print "Initializing World map script"
	global mc
	mc = MapConstants()
	mc.initInGameOptions()


def getGridSize(argsList):
	grid_sizes = {
		## Mini-Map Aspect Ratio Changed to 1.5
		WorldSizeTypes.WORLDSIZE_DUEL:		(12, 8),
		WorldSizeTypes.WORLDSIZE_TINY:		(18, 12),
		WorldSizeTypes.WORLDSIZE_SMALL:		(21, 14),
		WorldSizeTypes.WORLDSIZE_STANDARD:	(24, 16),
		WorldSizeTypes.WORLDSIZE_LARGE:		(27, 18),
		WorldSizeTypes.WORLDSIZE_HUGE:		(30, 20),
		6:									(33, 22),
		7:									(36, 24)
	}
	if (argsList[0] == -1): # (-1,) is passed to function on loads
			return []
	[eWorldSize] = argsList
	return grid_sizes[eWorldSize]


def getTopLatitude():
	return 90
def getBottomLatitude():
	return -90
def getWrapX():
	return mc.bWrapX
def getWrapY():
	return mc.bWrapY


def beforeGeneration():
	print "", "Preparing World map script generation"
	global mc
	if mc is None:
		print "Initializing World map script"
		mc = MapConstants()
		mc.initInGameOptions()
	mc.AdaptToGameOptions()
	PySeed()


def generatePlotTypes():
	timer0 = BugUtil.Timer('World Generation')
	global em, cm, tm, lm, rm, pb
	pb = PangaeaBreaker()
	print "Generate Elevation Map"
	timer = BugUtil.Timer('Generate Elevation map')
	em = ElevationMap()
	em.GenerateElevationMap()
	timer.log()
	print "\n", "Generate climate system"
	timer = BugUtil.Timer('Generate climate system')
	cm = ClimateMap()
	cm.GenerateTemperatureMap()
	cm.GenerateRainfallMap()
	timer.log()
	print "\n", "Generate Plot Map"
	timer = BugUtil.Timer('Generate Plot Map')
	tm = TerrainMap()
	tm.GeneratePlotMap()
	timer.log()
	print "\n", "Generate Terrain Map"
	timer = BugUtil.Timer('Generate Terrain Map')
	tm.GenerateTerrainMap()
	timer.log()
	print "\n", "Generate Lake Map"
	timer = BugUtil.Timer('Generate Lake Map')
	lm = LakeMap()
	lm.generateLakeMap()
	timer.log()
	print "\n", "Generate River Map"
	timer = BugUtil.Timer('Generate River Map')
	rm = RiverMap()
	rm.generateRiverMap()
	timer.log()
	if mc.bNewWorld:
		print "\n", "Defining New World"
		timer = BugUtil.Timer('Defining New World')
		coMa.generateContinentMap()
		timer.log()
	print "\n", "Generate Plot Types"
	timer = BugUtil.Timer('Generate Plot Types')
	plotTypes = [PlotTypes.PLOT_OCEAN] * mc.iArea
	plotData = tm.plotData
	PEAK = mc.PEAK
	HILL = mc.HILL
	LAND = mc.LAND
	n = 0
	for i in xrange(mc.iArea):
		if plotData[i]	 == PEAK:
			plotTypes[i] = PlotTypes.PLOT_PEAK
			n += 1
		elif plotData[i] == HILL:
			plotTypes[i] = PlotTypes.PLOT_HILLS
			n += 1
		elif plotData[i] == LAND:
			plotTypes[i] = PlotTypes.PLOT_LAND
			n += 1
	fWaterPercent = 1.0 - ( float(n) / float(mc.iArea) )
	timer.log()
	print "Water percent = %f" % fWaterPercent
	timer0.log()
	return plotTypes


def generateTerrainTypes():
	print "\n", "Generating Terrain Types"
	timer = BugUtil.Timer('Generate Terrain Types')
	GC = CyGlobalContext()

	terrDesert		= GC.getInfoTypeForString("TERRAIN_DESERT")
	terrSaltFlats	= GC.getInfoTypeForString("TERRAIN_SALT_FLATS")
	terrDunes		= GC.getInfoTypeForString("TERRAIN_DUNES")
	terrScrub		= GC.getInfoTypeForString("TERRAIN_SCRUB")
	terrRocky		= GC.getInfoTypeForString("TERRAIN_ROCKY")
	terrRockyArid	= GC.getInfoTypeForString("TERRAIN_BADLAND")
	terrRockyCold	= GC.getInfoTypeForString("TERRAIN_JAGGED")
	terrBarren		= GC.getInfoTypeForString("TERRAIN_BARREN")
	terrPlains		= GC.getInfoTypeForString("TERRAIN_PLAINS")
	terrIce			= GC.getInfoTypeForString("TERRAIN_ICE")
	terrPermaFrost	= GC.getInfoTypeForString("TERRAIN_PERMAFROST")
	terrTundra		= GC.getInfoTypeForString("TERRAIN_TUNDRA")
	terrTaiga		= GC.getInfoTypeForString("TERRAIN_TAIGA")
	terrGrass		= GC.getInfoTypeForString("TERRAIN_GRASSLAND")
	terrLush		= GC.getInfoTypeForString("TERRAIN_LUSH")
	terrMuddy		= GC.getInfoTypeForString("TERRAIN_MUDDY")
	terrMarsh		= GC.getInfoTypeForString("TERRAIN_MARSH")
	terrHill		= GC.getInfoTypeForString("TERRAIN_HILL")
	terrPeak		= GC.getInfoTypeForString("TERRAIN_PEAK")
	terrainShore	= GC.getInfoTypeForString("TERRAIN_LAKE_SHORE")
	terrainLake		= GC.getInfoTypeForString("TERRAIN_LAKE")
	terrCoast		= GC.getInfoTypeForString("TERRAIN_COAST")
	terrCoastPol	= GC.getInfoTypeForString("TERRAIN_COAST_POLAR")
	terrCoastTrop	= GC.getInfoTypeForString("TERRAIN_COAST_TROPICAL")
	terrSea			= GC.getInfoTypeForString("TERRAIN_SEA")
	terrSeaPol		= GC.getInfoTypeForString("TERRAIN_SEA_POLAR")
	terrSeaTrop		= GC.getInfoTypeForString("TERRAIN_SEA_TROPICAL")
	terrSeaDeep		= GC.getInfoTypeForString("TERRAIN_SEA_DEEP")
	terrSeaDeepP	= GC.getInfoTypeForString("TERRAIN_SEA_DEEP_POLAR")
	terrSeaDeepT	= GC.getInfoTypeForString("TERRAIN_SEA_DEEP_TROPICAL")
	terrOcean		= GC.getInfoTypeForString("TERRAIN_OCEAN")
	terrOceanPol	= GC.getInfoTypeForString("TERRAIN_OCEAN_POLAR")
	terrOceanTrop	= GC.getInfoTypeForString("TERRAIN_OCEAN_TROPICAL")
	terrTrench		= GC.getInfoTypeForString("TERRAIN_TRENCH")
	terrTrenchPol	= GC.getInfoTypeForString("TERRAIN_TRENCH_POLAR")
	terrTrenchTrop	= GC.getInfoTypeForString("TERRAIN_TRENCH_TROPICAL")

	terrTypes = array('H', [terrOcean] * mc.iArea)
	terrData = tm.terrData
	for i in xrange(mc.iArea):
		if terrData[i] == mc.OCEAN_POL:
			terrTypes[i] = terrOceanPol
		elif terrData[i] == mc.OCEAN_TROP:
			terrTypes[i] = terrOceanTrop
		elif terrData[i] == mc.TRENCH:
			terrTypes[i] = terrTrench
		elif terrData[i] == mc.TRENCH_POL:
			terrTypes[i] = terrTrenchPol
		elif terrData[i] == mc.TRENCH_TROP:
			terrTypes[i] = terrTrenchTrop
		elif terrData[i] == mc.SEA:
			terrTypes[i] = terrSea
		elif terrData[i] == mc.SEA_POL:
			terrTypes[i] = terrSeaPol
		elif terrData[i] == mc.SEA_TROP:
			terrTypes[i] = terrSeaTrop
		elif terrData[i] == mc.SEA_DEEP:
			terrTypes[i] = terrSeaDeep
		elif terrData[i] == mc.SEA_DEEP_P:
			terrTypes[i] = terrSeaDeepP
		elif terrData[i] == mc.SEA_DEEP_T:
			terrTypes[i] = terrSeaDeepT
		elif terrData[i] == mc.COAST:
			terrTypes[i] = terrCoast
		elif terrData[i] == mc.COAST_POL:
			terrTypes[i] = terrCoastPol
		elif terrData[i] == mc.COAST_TROP:
			terrTypes[i] = terrCoastTrop
		elif terrData[i] == mc.LAKE_SHORE:
			terrTypes[i] = terrainShore
		elif terrData[i] == mc.LAKE:
			terrTypes[i] = terrainLake
		elif terrData[i] == mc.DESERT:
			terrTypes[i] = terrDesert
		elif terrData[i] == mc.PLAINS:
			terrTypes[i] = terrPlains
		elif terrData[i] == mc.GRASS:
			terrTypes[i] = terrGrass
		elif terrData[i] == mc.TAIGA:
			terrTypes[i] = terrTaiga
		elif terrData[i] == mc.SALT_FLATS:
			terrTypes[i] = terrSaltFlats
		elif terrData[i] == mc.DUNES:
			terrTypes[i] = terrDunes
		elif terrData[i] == mc.SCRUB:
			terrTypes[i] = terrScrub
		elif terrData[i] == mc.ROCKY:
			terrTypes[i] = terrRocky
		elif terrData[i] == mc.ROCKY_ARID:
			terrTypes[i] = terrRockyArid
		elif terrData[i] == mc.ROCKY_COLD:
			terrTypes[i] = terrRockyCold
		elif terrData[i] == mc.BARREN:
			terrTypes[i] = terrBarren
		elif terrData[i] == mc.TUNDRA:
			terrTypes[i] = terrTundra
		elif terrData[i] == mc.LUSH:
			terrTypes[i] = terrLush
		elif terrData[i] == mc.MUDDY:
			terrTypes[i] = terrMuddy
		elif terrData[i] == mc.MARSH:
			terrTypes[i] = terrMarsh
		elif terrData[i] == mc.FROST:
			terrTypes[i] = terrPermaFrost
		elif terrData[i] == mc.ICE:
			terrTypes[i] = terrIce
	timer.log()
	return terrTypes


def addRivers():
	S = mc.S
	N = mc.N
	W = mc.W
	E = mc.E
	i = -1
	for y in xrange(mc.iHeight):
		for x in xrange(mc.iWidth):
			i += 1
			placeRiversInPlot(x, y, i, S, N, W, E)


def addLakes():
	return


def addFeatures():
	print "\n", "Generating Feature Types"
	timer = BugUtil.Timer('Generate Feature Types')
	GC = CyGlobalContext()
	MAP = GC.getMap()
	mapRand = GC.getGame().getMapRand()
	bGoodyHuts = True
	if CyGame().isOption(GameOptionTypes.GAMEOPTION_NO_GOODY_HUTS):
		bGoodyHuts = False
	impGoodyIsland		= GC.getInfoTypeForString("IMPROVEMENT_GOODY_ISLAND")
	featureForest		= GC.getInfoTypeForString("FEATURE_FOREST")
	featureJungle		= GC.getInfoTypeForString("FEATURE_JUNGLE")
	featureFloodPlains	= GC.getInfoTypeForString("FEATURE_FLOOD_PLAINS")
	featureOasis		= GC.getInfoTypeForString("FEATURE_OASIS")
	featureCactus		= GC.getInfoTypeForString("FEATURE_CACTUS")
	featureBog			= GC.getInfoTypeForString("FEATURE_PEAT_BOG")
	featureSwamp		= GC.getInfoTypeForString("FEATURE_SWAMP")
	featureIce			= GC.getInfoTypeForString("FEATURE_ICE")
	iWidth	= mc.iWidth
	iHeight = mc.iHeight

	FORESTLEAFY		= 0
	FORESTEVERGREEN	= 1
	FORESTSNOWY		= 2

	LAND	= mc.LAND
	WATER	= mc.WATER
	PEAK	= mc.PEAK
	BARREN		= mc.BARREN
	DESERT		= mc.DESERT
	DUNES		= mc.DUNES
	PLAINS		= mc.PLAINS
	SALT_FLATS	= mc.SALT_FLATS
	SCRUB		= mc.SCRUB
	ICE			= mc.ICE

	# Ocean Ice
	fTaigaTemp	= mc.TaigaTemp
	fTundraTemp = mc.TundraTemp
	fIceChanceMultiplier = mc.IceChanceMultiplier - 0.25 / (mc.iWorldSize + 1.0)
	if mc.bWrapY:
		finitIceChance = 0.6
	else:
		finitIceChance = 1.0
	fIceChance = finitIceChance
	fTempData = cm.TemperatureMap.data
	y = 0
	i = -1
	while fIceChance > 0.1:
		for x in xrange(iWidth):
			i += 1
			plot = MAP.plot(x, y)
			if plot.isWater() and random() < fIceChance and fTempData[i] < fTundraTemp:
				plot.setFeatureType(featureIce, 0)
		fIceChance *= fIceChanceMultiplier
		y += 1
	fIceChance = finitIceChance
	y = iHeight
	i = mc.iArea
	while fIceChance > 0.1:
		y -= 1
		for x in xrange(iWidth - 1, -1, -1):
			i -= 1
			plot = MAP.plot(x, y)
			if plot.isWater() and random() < fIceChance and fTempData[i] < fTundraTemp:
				plot.setFeatureType(featureIce, 0)
		fIceChance *= fIceChanceMultiplier
	# Land Features
	lushThreshold		= tm.lushThreshold
	plainsThreshold		= tm.plainsThreshold
	scrubThreshold		= tm.scrubThreshold
	desertThreshold		= tm.desertThreshold
	saltflatsThreshold	= tm.saltflatsThreshold
	fFloodplainChance	= mc.fFloodplainChance
	fOasisChance		= mc.fOasisChance
	fCactusChance		= mc.fCactusChance
	fForestTemp = mc.ForestTemp
	fJungleTemp = mc.JungleTemp
	fWoodFactor = mc.fWoodFactor
	fWoodChance = mc.fWoodChance
	pData = tm.plotData
	tData = tm.terrData
	i = -1
	for y in xrange(iHeight):
		for x in xrange(iWidth):
			i += 1
			plot = MAP.plot(x, y)
			iRainfall = cm.RainfallMap.data[i]
			# Floodplains & Oasis
			if pData[i] == LAND and tData[i] in (DESERT, DUNES, SCRUB, PLAINS):
				if plot.isRiver() and random() < fFloodplainChance:
					plot.setFeatureType(featureFloodPlains, 0)
				elif tData[i] != PLAINS:
					#is this square surrounded by dry land?
					bOasis = True
					bCactus = False
					for yy in xrange(y - 1, y + 2):
						for xx in xrange(x - 1, x + 2):
							ii = GetIndex(xx, yy)
							surPlot = MAP.plot(xx, yy)
							if pData[ii] != PEAK and tData[ii] not in (DESERT, DUNES, SALT_FLATS, SCRUB, BARREN, PLAINS):
								bOasis = False
							elif surPlot.isWater() == True:
								bOasis = False
							elif surPlot.getFeatureType() == featureOasis:
								bOasis = False
								bCactus = True
								break
							elif iRainfall > saltflatsThreshold and iRainfall < scrubThreshold:
								bCactus = True
						if bCactus and not bOasis:
							break
					if bOasis:
						if random() < fOasisChance:
							plot.setFeatureType(featureOasis, 0)
					elif bCactus:
						if random() < fCactusChance:
							plot.setFeatureType(featureCactus, 0)

			# Swamp & Bog
			iTemperature = cm.TemperatureMap.data[i]
			if iTemperature > fTundraTemp and pData[i] == LAND and tData[i] not in (DESERT, DUNES, SALT_FLATS, SCRUB):
				if ( iRainfall > lushThreshold ):
					if ( random() < 0.25 ):
						plot.setFeatureType(featureSwamp,0)
				elif ( iTemperature < fForestTemp ):
					if ( random() < 0.15 ):
						plot.setFeatureType(featureBog,0)
			# Other features
			if plot.getFeatureType() == FeatureTypes.NO_FEATURE:
				for iI in xrange(GC.getNumFeatureInfos()):
					if plot.canHaveFeature(iI):
						if random() * 10000 < GC.getFeatureInfo(iI).getAppearanceProbability():
							plot.setFeatureType(iI, -1)
			# Forest and Jungle
			if plot.getFeatureType() == FeatureTypes.NO_FEATURE and not plot.isPeak():
				if pData[i] != WATER and tData[i] not in (DESERT, DUNES, SALT_FLATS, SCRUB, ICE):
					if iRainfall > plainsThreshold * fWoodFactor and random() < fWoodChance:
						if iTemperature > fJungleTemp:
							if tData[i] == PLAINS:
								plot.setFeatureType(featureForest, FORESTLEAFY)
							else:
								plot.setFeatureType(featureJungle, 0)
						elif iTemperature > fForestTemp:
							plot.setFeatureType(featureForest, FORESTLEAFY)
						elif iTemperature > fTaigaTemp:
							plot.setFeatureType(featureForest, FORESTEVERGREEN)
						elif iTemperature > fTundraTemp:
							plot.setFeatureType(featureForest, FORESTSNOWY)
					elif iRainfall > desertThreshold:
						if iRainfall > random() * plainsThreshold * fWoodFactor / fWoodChance:
							if iTemperature > fForestTemp:
								 plot.setFeatureType(featureForest, FORESTLEAFY)
							elif iTemperature > fTaigaTemp:
								plot.setFeatureType(featureForest, FORESTEVERGREEN)
							elif iTemperature > fTundraTemp:
								plot.setFeatureType(featureForest, FORESTSNOWY)
				# Goody Islands
				elif (tData[i] >= mc.SEA and tData[i] <= mc.COAST_TROP) or tData[i] == mc.LAKE_SHORE:
					if bGoodyHuts and mapRand.get(19, 'GoodyIsland') == 0:
						plot.setImprovementType(impGoodyIsland)
	timer.log()


def addBonuses():
	if mc.fBonusMult:
		print "Bonus generation"
		timer = BugUtil.Timer('Bonus generation')
		bp.AddBonuses()
		timer.log()


def afterGeneration():
	#CvMapGeneratorUtil.placeC2CBonuses()
	NaturalWonders.NaturalWonders().placeNaturalWonders()


def assignStartingPlots():
	print "\n", "Starting plot finding"
	timer = BugUtil.Timer('Starting plot finding')
	spf.SetStartingPlots()
	timer.log()
	global mc, em, cm, tm, lm, rm, pb
	mc = em = cm = tm = lm = rm = pb = None
	print "|---------------------------|\n|\t\t^^ All done ^^\t\t|\n|---------------------------|"


def normalizeAddRiver(): return
def normalizeRemovePeaks(): return
def normalizeAddLakes(): return
def normalizeRemoveBadFeatures(): return
def normalizeRemoveBadTerrain(): return
def normalizeAddFoodBonuses(): return
def normalizeAddGoodTerrain(): return
def normalizeAddExtras():
	# This is the last function processed before the game begins.
	return

###############################################################################
## Additional Global functions
###############################################################################

def PySeed():
	#Python randoms are not usable in network games.
	#AIAndy - I disagree. Python randoms are deterministic so the only important thing is to seed from a synchronized source like MapRand.
	if CyGame().isNetworkMultiPlayer():
		#AIAndy - seed Python random with MapRand
		GC = CyGlobalContext()
		mapRand = GC.getGame().getMapRand()
		seedValue = mapRand.get(65535, "Seeding mapRand - FairWeather.py")
		seed(seedValue)
		mc.seedString = "Random seed (Using getMapRand) for this map is %(s)20d" % {"s" :seedValue}
	else:
		#Python 'long' has unlimited precision, while the random generator
		#has 53 bits of precision, so I'm using a 53 bit integer to seed the map!
		seed() #Start with system time
		seedValue = randint(0, 9007199254740991)
		seed(seedValue)
		mc.seedString = "Random seed (Using Python rands) for this map is %(s)20d" % {"s" :seedValue}


def GetIndex(x, y):
	iWidth = mc.iWidth
	if mc.bWrapX:
		xx = x % iWidth
	elif x < 0 or x >= iWidth:
		return -1
	else:
		xx = x
	if mc.bWrapY:
		yy = y % mc.iHeight
	elif y < 0 or y >= mc.iHeight:
		return -1
	else:
		yy = y
	return yy * iWidth + xx


'''
def GetOppositeDirection(direction):
	opposite = 0
	if direction == mc.N:
		opposite = mc.S
	elif direction == mc.S:
		opposite = mc.N
	elif direction == mc.E:
		opposite = mc.W
	elif direction == mc.W:
		opposite = mc.E
	elif direction == mc.NW:
		opposite = mc.SE
	elif direction == mc.SE:
		opposite = mc.NW
	elif direction == mc.SW:
		opposite = mc.NE
	elif direction == mc.NE:
		opposite = mc.SW
	return opposite
'''

def GetNeighbor(x, y, direction):
	if direction == 0:
		return x, y
	elif direction == mc.N:
		return x, y + 1
	elif direction == mc.S:
		return x, y - 1
	elif direction == mc.E:
		return x + 1, y
	elif direction == mc.W:
		return x - 1, y
	elif direction == mc.NE:
		return x + 1, y + 1
	elif direction == mc.NW:
		return x - 1, y + 1
	elif direction == mc.SE:
		return x + 1, y - 1
	elif direction == mc.SW:
		return x - 1, y - 1
	return -1, -1


def GetCoordFromIndex(i):
	x = i % mc.iWidth
	y = int(i / mc.iWidth)

	return (x, y)

def LinearMapping(a, b, val, c, d, bTruncate = True):
	"""
	Linearly maps a value relative to range [a, b] onto range [c, d], truncating unless bTruncate is passed False
	E.g. 13 from the range [10, 20] maps to 4.5 in the range [6, 1]; 9 would map to 6 unless bTruncate = False, which returns 7.5
	"""
	mappedVal = (val-a)/(b-a) * (d-c) + c
	if bTruncate:
		endLow  = min(c, d)
		endHigh = max(c, d)
		return max(endLow, min(endHigh, mappedVal))
	return mappedVal

def FindThresholdFromPercent(map, percent):
	if not map or percent >= 1:
		return -0.01
	if percent <= 0:
		return 1.01
	iLength = len(map)
	fPercentage = 1 - percent
	threshIndex = int(round((iLength-1) * fPercentage))
	mapTemp = []
	for i in xrange(iLength):
		mapTemp.append(map[i])
	mapTemp.sort()
	return mapTemp[int(threshIndex)]


# This function is a general purpose value tuner.
# It finds a value that will be greater than or less than the desired percent of a whole map within a given tolerance.
# Map values should be between 0 and 1. To exclude parts of the map, set them to value zero.
def FindValueFromPercent(map, percent):
	iArea = mc.iArea
	tolerance = percent / 25.0
	# To speed things up, we find the middle value in the dataset.
	minV = 100.0
	maxV = -100.0
	totalCount = 0.0
	for i in xrange(iArea):
		if map[i]:
			totalCount += 1.0
			if minV > map[i]:
				minV = map[i]
			if maxV < map[i]:
				maxV = map[i]
	mid = (maxV - minV) / 2.0 + minV
	threshold	   = mid
	thresholdChange = mid
	lastAdded	= False
	inTolerance = False
	iterations	= 0
	while True:
		iterations += 1
		if iterations > 500:
			print "can't find value within tolerance, end value = "
			print "threshold = %f, thresholdChange = %f" % (threshold, thresholdChange)
			break #close enough
		matchCount = 0
		for i in xrange(iArea):
			if map[i] and map[i] < threshold:
				matchCount += 1

		currentPercent = matchCount / totalCount
		if currentPercent < percent + tolerance and currentPercent > percent - tolerance:
			break
		if currentPercent > percent:
			threshold -= thresholdChange
			if lastAdded:
				#only cut thresholdChange when direction is changed
				thresholdChange /= 2.0
			lastAdded = False
		else:
			threshold += thresholdChange
			if not lastAdded:
				thresholdChange /= 2.0
			lastAdded = True
	#at this point value should be in tolerance or close to it
	return threshold


def isHmWaterMatch(x, y):
	i = GetIndex(x, y)
	if pb.distanceMap[i] > mc.iMinMeteorSize / 1.5:
		return True
	return False


def placeRiversInPlot(x, y, i, S, N, W, E):
	GC = CyGlobalContext()
	plot = GC.getMap().plot(x, y)
	ii = GetIndex(x, y + 1)
	if ii >= 0 and rm.riverMap[ii][0] == mc.S or rm.riverMap[ii][1] == S:
		plot.setWOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH)
	ii = GetIndex(x - 1, y)
	if ii >= 0 and rm.riverMap[ii][0] == mc.E or rm.riverMap[ii][1] == E:
		plot.setNOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_EAST)
	if rm.riverMap[i][0] == mc.N or rm.riverMap[i][1] == N:
		plot.setWOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_NORTH)
	if rm.riverMap[i][0] == mc.W or rm.riverMap[i][1] == W:
		plot.setNOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_WEST)