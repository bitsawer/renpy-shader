
# Rig Editor

This document provides some basic instructions for the rig editor. You can access the rig editor from the main menu. Make sure you have watched the [basic editor workflow video](https://www.youtube.com/watch?v=NHJu0OYBERE).

## Rigging walkthrough

You can play around with the demo project editor, but you probably want to rig your own files at some point. To do so:

* Place your image file(s) in the "images"-folder (or anywhere where they can be found by RenPy) and depending from your project config create an explicit image tag (normal or a LiveComposite) for them. It would be nice to work with all files and folders, but RenPy can do some very useful work for us this way.

* Add buttons to your game main menu (or anywhere else you like)

```python
    if renpy.config.developer:
        textbutton _("Start Rig Editor") action Start("start_editor")
        textbutton _("Reset window") action Function(renpy.reset_physical_size)
```

* The editor can change the size of the application window and sometimes it gets stuck in a wrong size. Press the "Reset Window" button to fix it.

* Start the editor.

* In the first dialog select the image tag you want to rig. Only choose a tag that references a real image file or a LiveComposite that contains image files.

* In the second dialog choose "Create a new rig". If you have previously saved a rig, you can choose it here. The editor can crash here if the image has some problematic areas (constructing the triangulated mesh from an arbitary image is tricky business). File a bug report (or contact me in another way) and send me the image that causes problems so I can hopefully fix the issue.

* If everything worked, rig away!

* Save the rig you created to a file. Now you can use the rig you just saved.

The saved .rig-file contains information about the RenPy images it was created from, so updating the image files afterwards can cause issues. Most importantly the image resolutions should not be changed. Changing colors or making small adjustments is usually fine, but you might need to re-adjust image edge points in the editor to re-triangulate the mesh if the image silhouette changed.

## Rigging tips

If some mesh part deforms in a bad way...

* Move the bone slightly. Sometimes the bone is just in a bad location and mesh deformation (like rotation) looks bad especially with large triangles nearby.

* Activate bone tessellation in spots that must deform alot, but be aware it can cause "holes" and tearing in the mesh if deformed enough. (To be fixed).

* Create "helper" bones to control the deformation between the bones you actually care about. Possibly enable tessellation on them, too.

* Combine translation with rotation. For example an elbow (or any other joint) bend animation can both rotate the joint and also move it slightly to fix or hide any bad spots.

* Adjust bone z-order to make sure the "better" bone hides the "bad" geometry under it.

* Try removing edge points around the important joint. Sometimes less dense mesh is actually better.

## Animation walkthrough

Bone attributes that can be animated:

* Rotation (x, y and z axis)
* Scaling (x, y and z axis)
* Translation (x and y axis)
* Visibility (visible / hidden)
* Transparency (alpha)

Keyframe animation is used. This means that keyframes for bones are inserted at important positions in the timeline and the frames between those keysframes are interpolated.

Playing the animation in the editor can be much slower (because of RenPy screen updates etc.) than playing it using the AnimationPlayer.

## Keyboard Shortcuts

The editor relies heavily on keyboard shortcuts.

### Rigging

* s: Scale active bone. While in this mode press x, y or z to only affect that axis. Left mouse click accepts, right cancels.
* s + alt: Clear active bone scaling.
* r: Rotate active bone. While in this mode press x, y or z to only affect that axis. Left mouse click accepts, right cancels.
* r + alt: Clear active bone rotation.
* g: Grab and translate active bone. While in this mode press x or y to only affect that axis. Left mouse click accepts, right cancels.
* g + alt: Clear active bone translation.
* a: Change the alpha transparency of active bone. Left mouse click accepts, right cancels.
* a + alt: Clear active bone alpha transparency.
* Mouse wheel: Increase or decrease active bone z-order. Changing the order also changes the order of all child bones.
* x: Delete the active bone (or an edge point if one is under the cursor).
* h: Toggle active bone hidden state.
* b: Toggle active bone blocker state.
* t: Toggle active bone tessellation state. This can be used to add more mesh detail to places that are heavily deformed (like joints). Can cause small "tearing" (or holes) to appear in the mesh when deformed. You can try add other tessellating bones nearby for a temporary workaround. To be fixed.
* d: Toggle active bone damping state. Very experimental! Might be removed in the future.
* e: Extrude a new child bone from the active bone. Left mouse click accepts, right cancels.
* c: Connect active bone into another parent bone. Left mouse click accepts, right cancels.

### Animation

* i: Insert a keyframe for the active bone at the current frame.
* i + alt: Delete active bone keyframe at the current frame.
* o: Toggle active bone cycle repeat animation state.
* p: Toggle active bone reverse animation state.
* j: Move one frame backwards.
* k: Start and stop the animation.
* l: Move one frame forward.

