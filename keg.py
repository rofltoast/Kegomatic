#!/usr/bin/python
import os
import time
import math
import logging
import pygame, sys
from pygame.locals import *
import RPi.GPIO as GPIO
from twitter import *
from flowmeter import *
from seekrits import *
from info import *
from thermometer import *

t = Twitter( auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET) )

boardRevision = GPIO.RPI_REVISION
GPIO.setmode(GPIO.BCM) # use real GPIO numbering
GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)#Set software pullup on pin 22
GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP)#Set software pullup on pin 23

# set up pygame
pygame.init()

# set up the window
VIEW_WIDTH = 1920
VIEW_HEIGHT = 1200
pygame.display.set_caption('KeggleBerry')

# hide the mouse
pygame.mouse.set_visible(False)

# set up the flow meters
fm = FlowMeter('right')#Default measurement is pints, swtich to 'metric' for L
fm2 = FlowMeter('left')#Default measurement is pints, swtich to 'metric' for L
temp = Temp()
tweet = ''

# set up the colors
BLACK = (0,0,0)
WHITE = (255,255,255)

# set up the window surface
windowSurface = pygame.display.set_mode((VIEW_WIDTH,VIEW_HEIGHT), FULLSCREEN, 32) 
windowInfo = pygame.display.Info()
FONTSIZE = 35
beerFONTSIZE = 98
basicFont = pygame.font.SysFont(None, FONTSIZE)
beerFont = pygame.font.SysFont(None, beerFONTSIZE)

def renderThings(flowMeter, flowMeter2, tweet, windowSurface, basicFont):
  # Clear the screen
  windowSurface.fill(BLACK)#No background image; black fill
  
  # Draw Beer Name Right Keg
  text = beerFont.render(Info.beerNameR, True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 80, 0))

  # Draw Beer Name Left Keg
  text = beerFont.render(Info.beerNameL, True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (80,0))
  
  #Draw temperature
  text = beerFont.render(temp.read_temp(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (945,0))  
  
  
  #########LEFT KEG#########
  # Draw Ammt Poured
  text = basicFont.render(flowMeter2.getFormattedThisPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (80,220))
  # Draw calories
  text = basicFont.render(flowMeter2.getFormattedCal(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (80,280))
  #Draw remaining
  text = basicFont.render(flowMeter2.getFormattedRemaining(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (50, 1000))

  #########RIGHT KEG#########
  # Draw Ammt Poured
  text = basicFont.render(flowMeter.getFormattedThisPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 80, 220))
  # Draw calories
  text = basicFont.render(flowMeter.getFormattedCal(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 80, 280))
  # Draw remaining
  text = basicFont.render(flowMeter.getFormattedRemaining(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 80, 1000))

  # Display everything
  pygame.display.flip()

# Beer, on Pin 22.
def doAClick(channel):
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  if fm.enabled == True:
    fm.update(currentTime)

# Beer, on Pin 23.
def doAClick2(channel):
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  if fm2.enabled == True:
    fm2.update(currentTime)

def tweetPour(theTweet):
  try:
    t.statuses.update(status=theTweet)
  except:
    logging.warning('Error tweeting: ' + theTweet + "\n")

GPIO.add_event_detect(22, GPIO.RISING, callback=doAClick, bouncetime=20)#Set 'rising edge' detection on pin 22
GPIO.add_event_detect(23, GPIO.RISING, callback=doAClick2, bouncetime=20)#Set 'rising edge' detection on pin 23

# main loop
while True:
  # Handle keyboard events
  for event in pygame.event.get():
    if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
      GPIO.cleanup()
      pygame.quit()
      sys.exit()
  
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  
  if (fm.thisPour > 0.05 and currentTime - fm.lastClick > 2000): # 2 seconds of inactivity causes a tweet
    tweet = "Someone just poured " + fm.getFormattedThisPour() + " of " + Info.beerNameR + " from the keg! " + "Only " + fm.getFormattedRemaining() + "!"
    ######insert SQL push here(thisPour)
    fm.thisPour = 0.0
    tweetPour(tweet)
 
  if (fm2.thisPour > 0.05 and currentTime - fm2.lastClick > 2000): # 2 seconds of inactivity causes a tweet
    tweet = "Someone just poured " + fm2.getFormattedThisPour() + " of " + Info.beerNameL + " from the keg! " + "Only " + fm2.getFormattedRemaining() + "!"
    ######insert SQL push here(thisPour)
    fm2.thisPour = 0.0
    tweetPour(tweet)

  # Update the screen
  renderThings(fm, fm2, tweet, windowSurface, basicFont)
