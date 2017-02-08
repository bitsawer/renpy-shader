
import renpy

import utils
from controller import RenderController, RenderContext, ControllerContextStore
from rendering import Renderer2D, Renderer3D, SkinnedRenderer
from shadercode import *

PROJECTION = "projection"

WORLD_MATRIX = "worldMatrix"
VIEW_MATRIX = "viewMatrix"
PROJ_MATRIX = "projMatrix"

TEX0 = "tex0"
TEX1 = "tex1"

MODE_2D = "2d"
MODE_3D = "3d"
MODE_SKINNED = "skinned"

ZERO_INFLUENCE = "zeroinfluence.png"

class config:
    enabled = True
    fps = 60
    flipMeshX = True

def log(message):
    renpy.display.log.write("Shaders: " + message)

def isSupported(verbose=False):
    if not config.enabled:
        if verbose:
            log("Disabled because of 'config.enabled'")
        return False

    if not renpy.config.gl_enable:
        if verbose:
            log("Disabled because of 'renpy.config.gl_enable'")
        return False

    renderer = renpy.display.draw.info.get("renderer") #TODO renpy.get_renderer_info()
    if renderer != "gl":
        if verbose:
            log("Disabled because the renderer is '%s'" % renderer)
        return False

    if verbose:
        log("Supported!")

    return True

_controllerContextStore = ControllerContextStore()

_coreSetMode = None
_coreSetModeCounter = 0

def _wrapSetMode(*args):
    global _coreSetModeCounter
    _coreSetModeCounter += 1

    _coreSetMode(*args)

def getModeChangeCount():
    return _coreSetModeCounter

#TERRBILE HACK!
#Mode change can reset the OpenGL context, so we need to track the
#mode change count in order to know when we must free and reload
#any OpenGL resources.

def _setupRenpyHooks():
    global _coreSetMode
    if _coreSetMode:
        #Already hooked
        return

    _coreSetMode = renpy.display.interface.set_mode
    renpy.display.interface.set_mode = _wrapSetMode
