
import euclid

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

class Frame:
    def __init__(self):
        self.keys = {}

    def getBoneKey(self, name):
        key = self.keys.get(name)
        if not key:
            key = KeyFrame()
            self.keys[name] = key
        return key

class SkinnedAnimation:
    def __init__(self):
        self.frames = [Frame()]

    def setFrameCount(self, count):
        self.frames = self.frames[:count]
        while len(self.frames) < count:
            self.frames.append(Frame())

    def canInsertBefore(self, frameNumber, bone):
        i = frameNumber - 1
        while i >= 0:
            frame = self.frames[i]
            if bone.name in frame.keys:
                key = frame.getBoneKey(bone.name)
                return keyDataChanged(key, bone)
            i -= 1
        return True

    def canInsertAfter(self, frameNumber, bone):
        i = frameNumber + 1
        while i < len(self.frames):
            frame = self.frames[i]
            if bone.name in frame.keys:
                key = frame.getBoneKey(bone.name)
                return keyDataChanged(key, bone)
            i += 1
        return True

    def findNewKeyFrames(self, frameNumber, bones):
        new = []
        changed = []
        frame = self.frames[frameNumber]
        for name in bones:
            key = frame.keys.get(name)
            if key is not None:
                if keyDataChanged(key, bones[name]):
                    changed.append(name)
            else:
                new.append(name)
        return new, changed

    def update(self, frameNumber, bones, editor):
        frame = self.frames[frameNumber]
        new, changed = self.findNewKeyFrames(frameNumber, bones)
        updated = [] + changed

        for name in new:
            bone = bones[name]
            if self.canInsertBefore(frameNumber, bone) and self.canInsertAfter(frameNumber, bone) or frameNumber == 0:
                updated.append(name)

        for name in updated:
            bone = bones[name]
            key = frame.getBoneKey(name)
            copyKeyData(bone, key)

        self.cleanupDuplicateKeys(bones, frameNumber)

        self.drawDebug(editor, frameNumber, changed)

    def cleanupDuplicateKeys(self, bones, frameNumber):
        for name, bone in bones.items():
            keys = self.getBoneKeyFrames(name)
            i = 0
            while i < len(keys):
                index = keys[i]
                i2 = i + 1
                duplicates = set()
                while i2 < len(keys):
                    index2 = keys[i2]
                    if not keyDataChanged(self.frames[index].keys[name], self.frames[index2].keys[name]):
                        if index == frameNumber:
                            duplicates.add(index)
                        elif index2 == frameNumber:
                            duplicates.add(index2)
                    i2 += 1
                i += 1

            for index in duplicates:
                if index > 0:
                    del self.frames[index].keys[name]

    def drawDebug(self, editor, frameNumber, changed):
        x = 10
        y = 10
        height = 20
        color = (255, 0, 0)

        editor.drawText("Frame: %i of %i" % (frameNumber, len(self.frames)), color, (x, y))
        y += height

        for i, name in enumerate(changed):
            editor.drawText(name, color, (x, y))
            y += height

        x = 200
        y = 10
        for i, frame in enumerate(self.frames):
            if i > 0 and frame.keys:
                editor.drawText("Frame %i:" % i, color, (x, y))
                y += height
                for name, key in frame.keys.items():
                    editor.drawText("Key %s" % name, (255, 255, 0), (x, y))
                    y += height

    def getBoneKeyFrames(self, name):
        results = []
        for i, frame in enumerate(self.frames):
            if name in frame.keys:
                results.append(i)
        return results

    def updateBones(self, bones):
        #TODO Remove frames that had their bones removed etc...
        pass

    def findKeyFrameRange(self, frameNumber, bone):
        start = None
        end = None

        i = frameNumber
        while i >= 0:
            if bone.name in self.frames[i].keys:
                start = i
                break
            i -= 1

        i = frameNumber
        while i < len(self.frames):
            if bone.name in self.frames[i].keys:
                end = i
                break
            i += 1

        return start, end

    def apply(self, frameNumber, bones):
        frame = self.frames[frameNumber]

        for name, bone in bones.items():
            start, end = self.findKeyFrameRange(frameNumber, bone)
            if start is not None and end is not None:
                key = self.frames[start].keys[name]
                copyKeyData(key, bone)
