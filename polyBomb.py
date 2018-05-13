import time
import math

from Xlib import XK, display
from Xlib.ext import record
from Xlib.protocol import rq


from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input



class Poly(object):
	"""docstring for Poly"""
	def __init__(self):
		super(Poly, self).__init__()
		self.d = display.Display()
		self.s = self.d.screen()
		self.root = self.s.root
		self.isMouseDown = False
		self.reset()
		self.zoom = 14

	def reset(self):
		self.left   = 1000000
		self.right  = 0
		self.top    = 1000000
		self.bottom = 0
		self.verts  = []

	def printVerts(self, verts):
		for v in verts:
			print("%d, %d," % (v[0], v[1]))

	def bomb(self, x, y):
		self.root.warp_pointer(x,y)
		time.sleep(0.01)
		self.d.sync()
		fake_input(self.d, X.ButtonPress, 1)
		self.d.sync()
		time.sleep(0.01)
		fake_input(self.d, X.ButtonRelease, 1)
		self.d.sync()
		time.sleep(0.005)

	def contains(self, x, y):
		i = 0
		c = 0
		for i in range(0, len(self.verts)):
			ax, ay = self.verts[i]
			px, py = self.verts[i-1]
			if (ay > y) != (py > y):
				if x < (px - ax) * (y - ay) / (float(py) - ay) + ax:
					c += 1
		return c % 2 == 1

	def getScale(self):
		return max(int(self.zoom**(2.7) / 90), 5)

	def addVert(self, x, y):
		scale = self.getScale()
		if len(self.verts) == 0 or (abs(x - self.verts[-1][0]) > scale * 2 or abs(y - self.verts[-1][1]) > scale * 2):
			self.left   = x if x < self.left   else self.left
			self.right  = x if x > self.right  else self.right
			self.top    = y if y < self.top    else self.top
			self.bottom = y if y > self.bottom else self.bottom
			self.verts.append((x,y))

	def polyBomb(self):
		scale = self.getScale()
		count = 0
		for mx in range(self.left, self.right, scale):
			for my in range(self.top, self.bottom, scale):
				if self.contains(mx, my):
					self.bomb(mx, my)
					count += 1
		return count

	def startPoly(self):
		self.isMouseDown = True

	def endPoly(self):
		self.isMouseDown = False
		if len(self.verts) > 2:
			print("Bombing: %d verts at %d zoom"%(len(self.verts), self.zoom))
			count = self.polyBomb()
			print("... %d artillery fired"% count)
		self.reset()

		#--- You can print verts out to plot in excel ---
		# self.printVerts(self.verts)







curPoly = Poly()



#=================================================
#
#  Below here is just copied from xlib tutorial
#
#-------------------------------------------------


local_dpy = display.Display()
record_dpy = display.Display()




def lookup_keysym(keysym):
	for name in dir(XK):
		if name[:3] == "XK_" and getattr(XK, name) == keysym:
			return name[3:]
	return "[%d]" % keysym


def record_callback(reply):
	global curPoly
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
			# pr = event.type == X.KeyPress and "Press" or "Release"

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
				# print("\tZoom: %d"%zoom)
			if event.detail == 4: # zoom in
				curPoly.zoom = min(curPoly.zoom + 1, 32)
				# print("\tZoom: %d"%zoom)

		elif event.type == X.ButtonRelease:
			# print("ButtonRelease", event.detail)
			if event.detail == 2:
				curPoly.endPoly()
				
		elif event.type == X.MotionNotify:
			# print("M``otionNotify", event.root_x, event.root_y)
			if curPoly.isMouseDown:
				curPoly.addVert(event.root_x, event.root_y)


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

