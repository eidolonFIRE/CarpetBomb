import time

from Xlib import XK, display
from Xlib.ext import record
from Xlib.protocol import rq

from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input

from Poly import Poly




def lookup_keysym(keysym):
	for name in dir(XK):
		if name[:3] == "XK_" and getattr(XK, name) == keysym:
			return name[3:]
	return "[%d]" % keysym


def record_callback(reply):
	global curPoly
	global record_dpy
	global local_dpy
	global ctx
	if reply.category != record.FromServer:
		return
	if reply.client_swapped:
		print("* received swapped protocol data, cowardly ignored")
		return
	if not len(reply.data) or reply.data[0] < 2:
		# not an event
		return

	data = reply.data
	while len(data):
		event, data = rq.EventField(None).parse_binary_value(data, record_dpy.display, None, None)
		if event.type in [X.KeyPress, X.KeyRelease]:
			keysym = local_dpy.keycode_to_keysym(event.detail, 0)
			# if not keysym:
			# 	print("KeyCode%s" % pr, event.detail)
			# else:
			# 	print("KeyStr%s" % pr, lookup_keysym(keysym))

			if event.type == X.KeyPress and lookup_keysym(keysym) == "n":
				curPoly.startPoly()
			if event.type == X.KeyRelease and lookup_keysym(keysym) == "n":
				curPoly.endPoly()

			# if event.type == X.KeyPress and keysym == XK.XK_Escape:
			if event.type == X.KeyPress and keysym == XK.XK_grave:
				local_dpy.record_disable_context(ctx)
				local_dpy.flush()
				return
		elif event.type == X.ButtonPress:
			# print("ButtonPress", event.detail)
			if event.detail == 2:
				curPoly.startPoly()

			if event.detail == 5: # zoom out
				curPoly.zoom = max(curPoly.zoom - 1, 1)
			if event.detail == 4: # zoom in
				curPoly.zoom = min(curPoly.zoom + 1, 32)

		elif event.type == X.ButtonRelease:
			# print("ButtonRelease", event.detail)
			if event.detail == 2:
				curPoly.endPoly()
				
		elif event.type == X.MotionNotify:
			# print("M``otionNotify", event.root_x, event.root_y)
			curPoly.addVert(event.root_x, event.root_y)


def bomb_callback(x, y):
	global d
	global root
	root.warp_pointer(x,y)
	time.sleep(0.01)
	d.sync()
	fake_input(d, X.ButtonPress, 1)
	d.sync()
	time.sleep(0.01)
	fake_input(d, X.ButtonRelease, 1)
	d.sync()
	# time.sleep(0.005)

curPoly = None
local_dpy = None
record_dpy = None
d = None
root = None
ctx = None


def main():
	global curPoly
	global local_dpy
	global record_dpy
	global d
	global root
	global ctx

	d = display.Display()
	s = d.screen()
	root = s.root
	curPoly = Poly(bomb_callback, d, root)

	local_dpy = display.Display()
	record_dpy = display.Display()

	# Check if the extension is present
	if not record_dpy.has_extension("RECORD"):
		print("RECORD extension not found")
	else:
		# r = record_dpy.record_get_version(0, 0)
		# print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))

		# Create a recording context; we only want key and mouse events
		ctx = record_dpy.record_create_context(
				0,
				[record.AllClients],
				[{
						'core_requests': (0, 0),
						'core_replies': (0, 0),
						'ext_requests': (0, 0, 0, 0),
						'ext_replies': (0, 0, 0, 0),
						'delivered_events': (0, 0),
						'device_events': (X.KeyPress, X.MotionNotify),
						'errors': (0, 0),
						'client_started': False,
						'client_died': False,
				}])

		# Enable the context; this only returns after a call to record_disable_context,
		# while calling the callback function in the meantime
		record_dpy.record_enable_context(ctx, record_callback)

		# Finally free the context
		record_dpy.record_free_context(ctx)



if __name__ == "__main__":
    # execute only if run as a script
    main()