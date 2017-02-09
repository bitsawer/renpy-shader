
import skin
import skinnedanimation
import euclid
import utils

FPS = 30.0

class TrackInfo:
    def __init__(self, name, repeat=False):
        self.name = name
        self.repeat = repeat
        self.reverse = False
        self.autoEnd = False

class Track:
    def __init__(self, info, startTime):
        self.info = info
        self.startTime = startTime
        self.animation = skinnedanimation.loadAnimationFromFile(utils.findFile(info.name + ".anim"))

    def getFrameIndex(self, currentTime):
        delta = currentTime - self.startTime
        frames = self.animation.frames
        frameCount = len(frames)
        return min(frameCount - 1, int(round(delta * FPS)))

    def isAtEnd(self, currentTime):
        index = self.getFrameIndex(currentTime)
        lastFrame = len(self.animation.frames) - 1
        return index >= lastFrame

class AnimationData:
    def __init__(self):
        self.tracks = {}

class AnimationPlayer:
    def __init__(self, context):
        self.context = context
        self.data = context.store.get("animationPlayer", AnimationData())
        context.store["animationPlayer"] = self.data

    def getTime(self):
        return self.context.time

    def startAnimation(self, info):
        track = Track(info, self.getTime())
        self.data.tracks[info.name] = track

    def stopAnimation(self, name):
        del self.data.tracks[name]

    def updateAnimations(self):
        tracks = list(self.data.tracks.values())
        tracks.sort(key=lambda t: t.info.name)
        for track in tracks:
            self.updateTrack(track)

    def updateTrack(self, track):
        frameIndex = track.getFrameIndex(self.getTime())
        #TODO apply should return the changes. then mix them together
        track.animation.apply(frameIndex, self.context.renderer.getBones()) #TODO Bakes every time...

    def play(self, infos, rest=True):
        for info in infos:
            if not info.name in self.data.tracks:
                self.startAnimation(info)

        self.updateAnimations()

        names = [i.name for i in infos]
        for name in self.data.tracks.copy():
            if not name in names:
                self.stopAnimation(name)

        if rest:
            self.restBones()

    def restBones(self):
        animated = self.getAnimatedBoneNames()
        bones = self.context.renderer.getBones()
        target = skin.SkinningBone(None)
        for name in bones:
            if not name in animated:
                self.restBone(bones[name], target)

    def restBone(self, a, b):
        weight = 0.1 #TODO Different speed for bones, use parent count etc.?
        a.translation = euclid.Vector3(*utils.interpolate3d(a.translation, b.translation, weight))
        a.rotation = euclid.Vector3(*utils.interpolate3d(a.rotation, b.rotation, weight))
        a.scale = euclid.Vector3(*utils.interpolate3d(a.scale, b.scale, weight))

    def getAnimatedBoneNames(self):
        names = set()
        for track in self.data.tracks.values():
            active = True
            if track.info.autoEnd:
                active = not track.isAtEnd(self.getTime())

            if active:
                for frame in track.animation.frames:
                    for name in frame.keys:
                        names.add(name)
        return names