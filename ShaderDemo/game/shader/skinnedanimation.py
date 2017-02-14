
import json
import pygame

import euclid
import utils
import skinnededitor
import easing

DEFAULT_EASING = "sineInOut"

class KeyFrame:
    def __init__(self):
        #self.pivot = None #TODO Can affect weight calculations
        self.translation = None
        self.rotation = None
        self.scale = None
        #self.zOrder = None #TODO Can't animate this efficiently, breaks vertex sorting...
        self.visible = None
        self.transparency = None

def copyKeyData(source, target):
    target.translation = euclid.Vector3(source.translation.x, source.translation.y, source.translation.z)
    target.rotation = euclid.Vector3(source.rotation.x, source.rotation.y, source.rotation.z)
    target.scale = euclid.Vector3(source.scale.x, source.scale.y, source.scale.z)
    target.visible = source.visible
    target.transparency = source.transparency

def interpolateKeyData(a, b, weight):
    key = KeyFrame()
    key.translation = euclid.Vector3(*utils.interpolate3d(a.translation, b.translation, weight))
    key.rotation = euclid.Vector3(*utils.interpolate3d(a.rotation, b.rotation, weight))
    key.scale = euclid.Vector3(*utils.interpolate3d(a.scale, b.scale, weight))
    key.visible = a.visible
    key.transparency = utils.interpolate(a.transparency, b.transparency, weight)
    return key

def mixKeys(keys, weights):
    result = KeyFrame()
    result.translation = euclid.Vector3(0, 0, 0)
    result.rotation = euclid.Vector3(0, 0, 0)
    result.scale = euclid.Vector3(1, 1, 1)
    result.visible = False
    result.transparency = 0.0
    for i, key in enumerate(keys):
        weight = weights[i]
        result.translation = result.translation + (key.translation * weight)
        result.rotation = result.rotation + (key.rotation * weight)
        result.scale = result.scale + (euclid.Vector3(key.scale.x - 1, key.scale.y - 1, key.scale.z - 1) * weight)
        result.visible = result.visible and key.visible
        result.transparency = result.transparency + (key.transparency * weight)
    return result

class Frame:
    def __init__(self):
        self.keys = {}

    def copy(self):
        copy = Frame()
        copy.keys = self.keys.copy()
        return copy

    def getBoneKey(self, name):
        key = self.keys.get(name)
        if not key:
            key = KeyFrame()
            self.keys[name] = key
        return key

class BoneData:
    def __init__(self):
        self.repeat = False
        self.reversed = False
        self.easing = DEFAULT_EASING

class SkinnedAnimation:
    jsonIgnore = ["dirty", "baked"]

    def __init__(self, name):
        self.name = name
        self.frames = [Frame()]
        self.boneData = {}
        self.dirty = True
        self.baked = None

    def isRepeating(self, name):
        data = self.boneData.get(name)
        if data:
            return data.repeat
        return False

    def isReversed(self, name):
        data = self.boneData.get(name)
        if data:
            return data.reversed
        return False

    def getEasing(self, name):
        data = self.boneData.get(name)
        if data:
            return data.easing
        return DEFAULT_EASING

    def getBoneData(self, name):
        data = self.boneData.get(name)
        if not data:
            data = BoneData()
            self.boneData[name] = data
        return data

    def setFrameCount(self, count):
        if count != len(self.frames):
            self.frames = self.frames[:count]
            while len(self.frames) < count:
                self.frames.append(Frame())
            self.dirty = True

    def update(self, frameNumber, editor):
        for event, pos in editor.context.events:
            if event.type == pygame.KEYDOWN:
                bone = editor.getActiveBone()
                key = event.key
                if key == pygame.K_i:
                    if bone:
                        if event.mod & pygame.KMOD_ALT:
                            if bone.name in self.frames[frameNumber].keys:
                                del self.frames[frameNumber].keys[bone.name]
                        else:
                            key = self.frames[frameNumber].getBoneKey(bone.name)
                            copyKeyData(bone, key)
                        self.dirty = True
                elif key == pygame.K_o:
                    if bone:
                        data = self.getBoneData(bone.name)
                        data.repeat = not data.repeat
                        self.dirty = True
                elif key == pygame.K_p:
                    if bone:
                        data = self.getBoneData(bone.name)
                        data.reversed = not data.reversed
                        self.dirty = True

    def drawDebugText(self, editor, frameNumber):
        color = skinnededitor.HEADER_COLOR
        align = 1
        x = editor.context.renderer.getSize()[0] - 10
        y = 10

        active = editor.getActiveBone()
        if active:
            y += editor.drawText("Keyframes", color, (x, y), align)[1]
            for i, frame in enumerate(self.frames):
                if active.name in frame.keys:
                    frameColor = (0, 0, 0)
                    if i == frameNumber:
                        frameColor = skinnededitor.ACTIVE_COLOR
                    y += editor.drawText("%i" % i, frameColor, (x, y), align)[1]
        else:
            for i, frame in enumerate(self.frames):
                if frame.keys: # i > 0 and
                    frameColor = color
                    if i == frameNumber:
                        frameColor = skinnededitor.ACTIVE_COLOR

                    y += editor.drawText("Frame %i" % i, frameColor, (x, y), align)[1]
                    for name, key in frame.keys.items():
                        y += editor.drawText("%s" % name, (0, 0, 0), (x, y), align)[1]

    def drawDebugKeyFrames(self, editor, frameNumber):
        keyframes = set()
        currents = set()
        bones = editor.getBones()
        for name, bone in bones.items():
            for i, frame in enumerate(self.frames):
                if name in frame.keys:
                    if i == frameNumber:
                        currents.add(name)
                    else:
                        keyframes.add(name)

        for name in keyframes:
            self.drawDebugBone(editor, bones, name, False)

        for name in currents:
            self.drawDebugBone(editor, bones, name, True)

    def drawDebugBone(self, editor, bones, boneName, hasKeyframe):
        pos = editor.getBonePivotTransformed(bones[boneName])
        size = skinnededitor.PIVOT_SIZE * 2 + 1
        color = (255, 255, 0)
        if hasKeyframe:
            color = (0, 255, 0)

        editor.context.overlayCanvas.circle(color, (pos.x, pos.y), size, 1)

        offset = 3
        if self.isRepeating(boneName):
            offset += 3
            editor.context.overlayCanvas.circle((255, 255, 0), (pos.x, pos.y), size + 3, 1)

        if self.isReversed(boneName):
            points = [(pos.x - size - offset, pos.y + size), (pos.x - size - offset, pos.y - size)]
            editor.context.overlayCanvas.lines((255, 255, 0), False, points, 2)

    def getBoneKeyFrames(self, name):
        results = []
        for i, frame in enumerate(self.frames):
            if name in frame.keys:
                results.append(i)
        return results

    def getKeyBones(self):
        bones = set()
        for frame in self.frames:
            for name in frame.keys:
                bones.add(name)
        return bones

    def renameBone(self, oldName, newName):
        for frame in self.frames:
            if oldName in frame.keys:
                key = frame.keys[oldName]
                del frame.keys[oldName]
                frame.keys[newName] = key

    def reverseKeyFrames(self, frames, keyFrames, name):
        keys = {}
        for index in keyFrames:
            keys[index] = frames[index].keys[name]
            del frames[index].keys[name]

        first = keyFrames[0]
        last = keyFrames[-1]
        results = []
        for index in keyFrames:
            newIndex = first + (index - last)
            frames[newIndex].keys[name] = keys[index]
            results.append(newIndex)

        return sorted(results)

    def bakeFrames(self):
        baked = []
        for frame in self.frames:
            baked.append(frame.copy())

        keyBones = self.getKeyBones()
        for name in keyBones:
            boneFrames = self.getBoneKeyFrames(name)

            if len(boneFrames) > 1 and self.isReversed(name):
                boneFrames = self.reverseKeyFrames(baked, boneFrames, name)

            if len(boneFrames) > 1 and self.isRepeating(name):
                current = len(boneFrames) - 1
                step = -1
                i = boneFrames[-1]
                while i < len(self.frames):
                    index = boneFrames[current]
                    #copyKeyData(self.frames[index].keys[name], baked[i].getBoneKey(name))
                    copyKeyData(baked[index].keys[name], baked[i].getBoneKey(name))

                    current += step
                    if current == -1:
                        current = 1
                        step = 1
                    elif current == len(boneFrames):
                        current = len(boneFrames) - 2
                        step = -1

                    jump = abs(boneFrames[current] - index)
                    i += jump

        return baked, keyBones

    def updateBaked(self):
        if self.dirty or not self.baked:
            self.baked = self.bakeFrames()
        self.dirty = False

    def findKeyFrameRange(self, frames, frameNumber, boneName):
        start = None
        end = None

        #TODO modulo frame search?
        i = frameNumber
        while i >= 0 and i < len(frames):
            if boneName in frames[i].keys:
                start = i
                break
            i -= 1

        for i in range(frameNumber, frameNumber + len(frames)):
            index = i % len(frames)
            if boneName in frames[index].keys:
                end = (index, i)
                break

        return start, end

    def clipEnd(self):
        i = len(self.frames) - 1
        while i > 0:
            if len(self.frames[i].keys) != 0:
                break
            i -= 1
        self.frames = self.frames[:i + 2]
        self.dirty = True
        return len(self.frames)

    def interpolate(self, frameNumber, bones, easingOverride=None):
        self.updateBaked()

        results = {}
        frames, keyBones = self.baked
        for name, bone in bones.items():
            if name in keyBones:
                start, end = self.findKeyFrameRange(frames, frameNumber, bone.name)
                if start is not None and end is not None:
                    startKey = frames[start].keys[name]
                    endKey = frames[end[0]].keys[name]
                    weight = float(frameNumber - start) / max(end[1] - start, 1.0)
                    boneEasing = easingOverride
                    if not boneEasing:
                        boneEasing = self.getEasing(bone.name)
                    eased = easing.getEasing(boneEasing)(weight)
                    results[name] = interpolateKeyData(startKey, endKey, eased)
        return results

    def apply(self, keys, bones):
        for name, key in keys.items():
            if name in bones:
                copyKeyData(key, bones[name])


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (KeyFrame, Frame, BoneData, SkinnedAnimation)):
            d = obj.__dict__.copy()
            for ignore in getattr(obj, "jsonIgnore", []):
                if ignore in d:
                    del d[ignore]
            return d
        elif isinstance(obj, euclid.Vector3):
            return (obj.x, obj.y, obj.z)
        elif isinstance(obj, ctypes.Array):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

DEPRECATED = []

def checkJson(obj, data):
    ignores = getattr(obj, "jsonIgnore", []) + DEPRECATED
    for key in data:
        if not key in obj.__dict__ and key not in ignores:
            name = obj.__class__.__name__
            raise RuntimeError("Key '%s' in JSON but not in object '%s'" % (key, name))

VERSION = 1

def saveAnimationToFile(path, animation):
    data = {
        "version": VERSION,
        "animation": animation,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=1, cls=JsonEncoder, separators=(",", ": "), sort_keys=True)

def loadAnimationFromFile(path):
    data = None
    with utils.openFile(path) as f:
        data = json.load(f)

    if data["version"] != VERSION:
        raise RuntimeError("Incompatible animation format version, should be %i" % VERSION)

    data = data["animation"]
    anim = SkinnedAnimation(data["name"])
    anim.dirty = True

    anim.frames = []
    for f in data["frames"]:
        frame = Frame()
        for name, key in f["keys"].items():
            keyFrame = KeyFrame()
            keyFrame.translation = euclid.Vector3(*key["translation"])
            keyFrame.rotation = euclid.Vector3(*key["rotation"])
            keyFrame.scale = euclid.Vector3(*key["scale"])
            keyFrame.visible = key["visible"]
            keyFrame.transparency = key["transparency"]
            checkJson(keyFrame, key)
            frame.keys[name] = keyFrame
        checkJson(frame, f)
        anim.frames.append(frame)

    anim.boneData = {}
    for name, entry in data["boneData"].items():
        boneData = BoneData()
        boneData.repeat = entry["repeat"]
        boneData.reversed = entry["reversed"]
        boneData.easing = entry["easing"]
        checkJson(boneData, entry)
        anim.boneData[name] = boneData

    checkJson(anim, data)

    return anim
