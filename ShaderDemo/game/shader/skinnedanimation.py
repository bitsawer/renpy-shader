
import pygame
import euclid
import utils
import skinnededitor
import easing

class KeyFrame:
    def __init__(self):
        self.pivot = None
        self.rotation = None
        self.scale = None
        self.zOrder = None
        self.visible = None

def copyKeyData(source, target):
    target.pivot = (source.pivot[0], source.pivot[1])
    target.rotation = euclid.Vector3(source.rotation.x, source.rotation.y, source.rotation.z)
    target.scale = euclid.Vector3(source.scale.x, source.scale.y, source.scale.z)
    target.zOrder = source.zOrder
    target.visible = source.visible

def keyDataChanged(a, b):
    if a.pivot != b.pivot:
        return True
    if a.rotation != b.rotation:
        return True
    if a.scale != b.scale:
        return True
    if a.zOrder != b.zOrder:
        return True
    if a.visible != b.visible:
        return True
    return False

def interpolateKeyData(a, b, weight):
    key = KeyFrame()
    key.pivot = utils.interpolate2d(a.pivot, b.pivot, weight)
    key.rotation = euclid.Vector3(*utils.interpolate3d(a.rotation, b.rotation, weight))
    key.scale = euclid.Vector3(*utils.interpolate3d(a.scale, b.scale, weight))
    key.zOrder = a.zOrder
    key.visible = a.visible
    return key

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

DEFAULT_EASING = "outBack"

class BoneData:
    def __init__(self):
        self.repeat = True
        self.easing = DEFAULT_EASING

class SkinnedAnimation:
    def __init__(self, name):
        self.name = name
        self.frames = [Frame()]
        self.boneData = {}

    def isRepeating(self, name):
        data = self.boneData.get(name)
        if not data or data.repeat:
            return True
        return False

    def getEasing(self, name):
        data = self.boneData.get(name)
        if data:
            return data.easing
        return DEFAULT_EASING

    def setFrameCount(self, count):
        self.frames = self.frames[:count]
        while len(self.frames) < count:
            self.frames.append(Frame())

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
                elif key == pygame.K_m:
                    if bone:
                        data = self.boneData.get(bone.name)
                        if not data:
                            data = BoneData()
                            self.boneData[bone.name] = data
                        data.repeat = not data.repeat

        self.cleanupDuplicateKeys(editor.getBones(), frameNumber)

    def cleanupDuplicateKeys(self, bones, frameNumber):
        for name, bone in bones.items():
            keys = self.getBoneKeyFrames(name)
            duplicates = set()
            i = 0
            while i < len(keys):
                index = keys[i]
                i2 = i + 1

                while i2 < len(keys):
                    index2 = keys[i2]
                    if not keyDataChanged(self.frames[index].keys[name], self.frames[index2].keys[name]):
                        if index == frameNumber:
                            duplicates.add(index)
                        elif index2 == frameNumber:
                            duplicates.add(index2)
                    else:
                        break
                    i2 += 1
                i += 1

            for index in duplicates:
                if index > 0:
                    del self.frames[index].keys[name]

    def drawDebugText(self, editor, frameNumber):
        height = 20
        color = (0, 255, 0)
        align = 1
        x = editor.context.renderer.getSize()[0] - 10
        y = 10

        active = editor.getActiveBone()
        if active:
            editor.drawText("Keys for bone '%s'" % active.name, (0, 255, 0), (x, y), align)
            y += height
            for i, frame in enumerate(self.frames):
                if active.name in frame.keys:
                    editor.drawText("%i" % i, (0, 0, 0), (x, y), align)
                    y += height
        else:
            for i, frame in enumerate(self.frames):
                if frame.keys: # i > 0 and
                    editor.drawText("Frame %i" % i, color, (x, y), align)
                    y += height
                    for name, key in frame.keys.items():
                        editor.drawText("%s" % name, (0, 0, 0), (x, y), align)
                        y += height

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
        size = skinnededitor.PIVOT_SIZE * 2
        color = (255, 255, 0)
        if hasKeyframe:
            color = (0, 255, 0)

        if self.isRepeating(boneName):
            editor.context.overlayCanvas.circle(color, (pos.x, pos.y), size, 1)
        else:
            editor.context.overlayCanvas.rect(color, (pos.x - size, pos.y - size, size * 2, size * 2), 1)

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
        return list(bones)

    def renameBone(self, oldName, newName):
        for frame in self.frames:
            if oldName in frame.keys:
                key = frame.keys[oldName]
                del frame.keys[oldName]
                frame.keys[newName] = key

    def updateBones(self, bones):
        #TODO Remove frames that had their bones:
        # -removed
        # -renamed
        # -etc...
        pass

    def bakeFrames(self):
        baked = []
        for frame in self.frames:
            baked.append(frame.copy())

        for name in self.getKeyBones():
            boneFrames = self.getBoneKeyFrames(name)

            if len(boneFrames) > 1 and self.isRepeating(name):
                current = len(boneFrames) - 1
                step = -1
                i = boneFrames[-1]
                while i < len(self.frames):
                    index = boneFrames[current]
                    copyKeyData(self.frames[index].keys[name], baked[i].getBoneKey(name))

                    current += step
                    if current == -1:
                        current = 1
                        step = 1
                    elif current == len(boneFrames):
                        current = len(boneFrames) - 2
                        step = -1

                    jump = abs(boneFrames[current] - index)
                    i += jump

                missing = i - len(self.frames)
                if missing > 0:
                    #Add a keyframe to smooth the transition back to frame 0
                    start, end = self.findKeyFrameRange(self.frames, boneFrames[0], name)
                    if end is not None:
                        copyKeyData(self.frames[end].keys[name], baked[len(baked) - 1].getBoneKey(name))

        return baked

    def findKeyFrameRange(self, frames, frameNumber, boneName):
        start = None
        end = None

        #TODO modulo frame search?
        i = frameNumber
        while i >= 0:
            if boneName in frames[i].keys:
                start = i
                break
            i -= 1

        i = frameNumber
        while i < len(frames):
            if boneName in frames[i].keys:
                end = i
                break
            i += 1

        return start, end

    def debugBake(self, editor):
        baked = self.bakeFrames()

        x = 400
        y = 10
        for i, frame in enumerate(baked):
            for name, key in frame.keys.items():
                editor.drawText("Baked: %s - %s" % (i, name), (0, 0, 0), (x, y))
                y += 20


    def apply(self, frameNumber, bones):
        baked = self.bakeFrames()

        for name, bone in bones.items():
            start, end = self.findKeyFrameRange(baked, frameNumber, bone.name)
            if start is not None and end is not None:
                startKey = baked[start].keys[name]
                endKey = baked[end].keys[name]
                if startKey == endKey:
                    copyKeyData(startKey, bone)
                else:
                    weight = float(frameNumber - start) / (end - start)
                    eased = easing.EASINGS[self.getEasing(bone.name)](weight)
                    key = interpolateKeyData(startKey, endKey, eased)
                    copyKeyData(key, bone)
