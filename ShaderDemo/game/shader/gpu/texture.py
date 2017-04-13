
import ctypes
from OpenGL import GL as gl

class Texture:
    def __init__(self, surface):
        self.width = 0
        self.height = 0
        self.textureId = 0

        self._load(surface)

    def _load(self, surface):
        self.free()

        self.width = surface.get_width()
        self.height = surface.get_height()
        self.textureId = 0

        textureId = (gl.GLuint * 1)()

        surface.lock()

        BYTEP = ctypes.POINTER(ctypes.c_ubyte)
        ptr = ctypes.cast(surface._pixels_address, BYTEP)

        gl.glGenTextures(1, textureId)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glActiveTexture(gl.GL_TEXTURE0)

        gl.glPixelStorei(gl.GL_UNPACK_ROW_LENGTH, surface.get_pitch() // surface.get_bytesize())
        gl.glBindTexture(gl.GL_TEXTURE_2D, textureId[0])
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, ptr)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);
        gl.glPixelStorei(gl.GL_UNPACK_ROW_LENGTH, 0)

        surface.unlock()

        self.textureId = textureId[0]

    def free(self):
        if self.textureId:
            gl.glDeleteTextures(1, self.textureId)
            self.textureId = 0

    def valid(self):
        return self.textureId != 0

    def bind(self, index):
        gl.glActiveTexture(gl.GL_TEXTURE0 + index)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureId)
