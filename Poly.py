import math


def _vertSub(a, b):
	return a[0] - b[0], a[1] - b[1]

def _vertAtan2(a, b):
	return math.atan2(b[1] - a[1], b[0] - a[0])

def _vertNorm(a, b):
	return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

class Poly(object):
	"""docstring for Poly"""
	def __init__(self, bomb_callback=None, display=None, root=None):
		super(Poly, self).__init__()
		self.d = display
		self.root = root
		self.started = False
		self._reset()
		self.zoom = 16
		self.bomb = bomb_callback

	def _reset(self):
		self.left   = 1000000
		self.right  = 0
		self.top    = 1000000
		self.bottom = 0
		self.verts  = []

	def printVerts(self, verts, indent = 0):
		i = 0
		for v in verts:
			print(("%d, " + ","*indent + " %d") % (v[0], v[1]))
			i += 1

	def _contains(self, x, y):
		i = 0
		c = 0
		for i in range(0, len(self.verts)):
			ax, ay = self.verts[i]
			px, py = self.verts[i-1]
			if (ay > y) != (py > y):
				if x < (px - ax) * (y - ay) / (float(py) - ay) + ax:
					c += 1
		return c % 2 == 1

	def _getScale(self):
		return max(int(self.zoom**(2.7) / 90), 5)

	def douglasPeuckerReduceVerts(self, epsilon, verbose=True):
		prevCount = len(self.verts)
		self.verts, iterCounter = self._douglasPeucker(self.verts, epsilon)
		postCount = len(self.verts)
		if verbose:
			print("Vert reduction: %d --> %d in %d steps" % (prevCount, postCount, iterCounter))

	def _douglasHeuristic(self, origin, point, end):
		return abs(math.sin(abs(_vertAtan2(origin, point) - _vertAtan2(origin, end))) * _vertNorm(origin, point))

	def _douglasPeucker(self, verts, epsilon):
		# https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
		# Find the point with the maximum distance
		iterCounter = 0
		dmax = 0
		index = 0
		for scan in range(1, len(verts) - 1):
			iterCounter += 1
			d = self._douglasHeuristic(verts[0], verts[scan], verts[-1])
			if d > dmax:
				index = scan
				dmax = d
		# If max distance is greater than epsilon, recursively simplify
		if dmax > epsilon:
			# Recursive call
			recResults1, z1 = self._douglasPeucker(verts[:index + 1], epsilon)
			recResults2, z2 = self._douglasPeucker(verts[index:], epsilon)
			iterCounter += z1 + z2
			retval = recResults1[:-1] + recResults2
		else:
			retval = [verts[0], verts[-1]]

		return retval, iterCounter


	def addVert(self, x, y):
		if self.started:
			if len(self.verts) == 0 or (abs(x - self.verts[-1][0]) > 2 or abs(y - self.verts[-1][1]) > 2):
				self.left   = x if x < self.left   else self.left
				self.right  = x if x > self.right  else self.right
				self.top    = y if y < self.top    else self.top
				self.bottom = y if y > self.bottom else self.bottom
				self.verts.append((x,y))

	def polyBomb(self):
		scale = self._getScale()
		count = 0
		offsetRow = True
		if self.bomb:
			for mx in range(self.left, self.right, scale):
				offsetRow = not offsetRow
				for my in range(self.top  - (scale / 2 * offsetRow), self.bottom, scale):
					if self._contains(mx, my):
						self.bomb(mx, my)
						count += 1
						if count >= 1000:
							print("Failsafe due to >1000 launches...")
							return count
		return count

	def startPoly(self):
		self.started = True

	def endPoly(self):
		self.started = False
		if len(self.verts) > 5:
			self.douglasPeuckerReduceVerts(epsilon=2.7, verbose=False)
			count = self.polyBomb()
			print("- %d Artillery launched at %d zoom"%(count, self.zoom))
		
		self._reset()
