import skin
import skinnedanimation
import euclid
import utils


class TrackInfo:
    def __init__(self, name, repeat=False, cyclic=False, reverse=False, autoEnd=False,
            clip=False, weight=1.0, speed=1.0, fps=30, easingOverride=None):
        self.name = name
        self.repeat = repeat
        self.cyclic = cyclic
        self.reverse = reverse
        self.autoEnd = autoEnd
        self.clip = clip
        self.weight = weight
        self.speed = speed
        self.fps = float(fps)
        self.easingOverride = easingOverride


class Track:
    def __init__(self, info, startTime):
        self.info = info
        self.startTime = startTime
        self.animation = skinnedanimation.loadAnimationFromFile(utils.findFile(info.name))
        if self.info.clip:
            self.animation.clipEnd()

    def getFrameIndex(self, currentTime):
        delta = (currentTime - self.startTime) * self.info.speed
        return int(round(delta * self.info.fps))

    def getFrameIndexClamped(self, currentTime):
        index = self.getFrameIndex(currentTime)
        frameCount = len(self.animation.frames)
        return min(frameCount - 1, index)

    def getFrameIndexRepeat(self, currentTime):
        index = self.getFrameIndex(currentTime)
        return index % len(self.animation.frames)

    def getFrameIndexCyclic(self, currentTime):
        index = self.getFrameIndex(currentTime)
        frameCount = len(self.animation.frames)
        reversing = (index // frameCount) % 2
        realIndex = index % frameCount
        if reversing:
            return (frameCount - 1) - realIndex
        else:
            return realIndex

    def isAtEnd(self, currentTime):
        index = self.getFrameIndexClamped(currentTime)
        lastFrame = len(self.animation.frames) - 1
        return index >= lastFrame


class AnimationData:
    def __init__(self):
        self.tracks = {}


class AnimationPlayer:
    def __init__(self, context, tag, reset=False):
        self.context = context
        self.tag = tag
        self.debug = False
        self.debugY = 10

        fullTag = "animationPlayer-" + tag
        if reset:
            self.data = AnimationData()
        else:
            self.data = context.store.get(fullTag, AnimationData())
        context.store[fullTag] = self.data

    def setDebug(self, debug):
        self.debug = debug

    def getTime(self):
        return self.context.shownTime

    def getTrackInfo(self, name):
        track = self.data.tracks.get(name)
        if track:
            return track.info
        return None

    def startAnimation(self, info):
        track = Track(info, self.getTime())
        self.data.tracks[info.name] = track

    def stopAnimation(self, name):
        del self.data.tracks[name]

    def updateAnimations(self):
        tracks = list(self.data.tracks.values())
        tracks.sort(key=lambda t: t.info.name)

        mix = {}
        for track in tracks:
            keys = self.updateTrack(track)
            if keys:
                for name, key in keys.items():
                    d = mix.get(name, [])
                    d.append((track, key))
                    mix[name] = d

        self.mixTrackKeys(mix)

    def updateTrack(self, track):
        currentTime =  self.getTime()
        if track.info.autoEnd and track.isAtEnd(currentTime):
            self.debugDraw(track, "(Autoend)")
            return None

        if track.info.cyclic:
            frameIndex = track.getFrameIndexCyclic(currentTime)
        elif track.info.repeat:
            frameIndex = track.getFrameIndexRepeat(currentTime)
        else:
            frameIndex = track.getFrameIndexClamped(currentTime)

        if track.info.reverse:
            frameIndex = (len(track.animation.frames) - 1) - frameIndex

        keys = track.animation.interpolate(frameIndex, self.context.renderer.getBones(), track.info.easingOverride)

        self.debugDraw(track, frameIndex)

        return keys

    def mixTrackKeys(self, mix):
        bones = self.context.renderer.getBones()
        for name, bone in bones.items():
            data = mix.get(name)
            if data:
                weights = [d[0].info.weight for d in data]
                keys = [d[1] for d in data]
                mixed = skinnedanimation.mixKeys(keys, weights)
                skinnedanimation.copyKeyData(mixed, bone)

    def debugDraw(self, track, frameIndex):
        if self.debug:
            self.context.createOverlayCanvas()
            # TODO Also tell how many keys reference missing bones
            text = "%s (%s) Speed: %.1f, Frame %s / %i" % (self.tag, track.info.name,
                track.info.speed, frameIndex, len(track.animation.frames) - 1)
            pos = (10, self.debugY)
            color = (0, 0, 0)
            self.debugY += utils.drawText(self.context.overlayCanvas, text, pos, color)[1]

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
        weight = 0.1  # TODO Different speed for bones, use parent count etc.?
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
