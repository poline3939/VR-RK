import numpy as np

def help(module):
	if module=="sp_hamonics":
		print("This function is used to calculate spherical harmonics of a volume")
		print("    -> Input: data (input dataset, dict, {'volume':[...], 'mask':[...]}), set 'mask' as None if data doesn't need a mask")
		print("              r (int/float, radius of the shell you want to expand, in pixels)")
		print("     *option: L (int, level of hamonics, default is 10)")
		print("    -> Return: shdes (numpy.ndarray, shape=(L,))")
		print("[Notice] The volume/mask inside data should be 3-dimensional matrix")
		return
	else:
		raise ValueError("No module names "+str(module))

class _sphere_des():
	# spherical polym descriptor
	from scipy.special import sph_harm
	import sys
	import os
	import h5py
	import scipy
	sys.path.append(__file__.split('/analyse/SH_expan.py')[0] + '/image')
	import q
	import radp
	import orientation
	import numpy as np

	def __init__(self):
		self.data = None
		self.mask = None
		self.exparam = None
		self.L = None
		self.rmax = None
		self.r = None
		self.qinfo = None
		self.dsize = None
		self.Clm = None
		self.Cl = None
		self.data_center = None

	def load_data(self, dataset):
		try:
			self.data = dataset['volume']
			self.mask = dataset['mask']
			if self.mask is not None:
				self.data = self.data * self.mask
		except:
			print("\nInput dataset format : ")
			print("--- dict")
			print("     |- 'volume' : numpy.ndarray(size0, size1, size2)")
			print("     |- 'mask' : numpy.ndarray(size1, size2) or None\n")
			raise ValueError("Input data file format error. Exit")
		self.data_center = (self.data.shape[0]/2,self.data.shape[1]/2,self.data.shape[2]/2)
		self.dsize = self.data.shape
		self.rmax = min(self.dsize) - max(self.data_center)
	
	def _cal_one_point(self, pointx, pointy, pointz, m, l):
		theta,phi = self.orientation._xyz2ang([pointx, pointy, pointz], self.data_center)
		sh = self.sph_harm(m,l,theta,phi)
		return sh.conjugate()

	def compute(self, L, r):
		self.L = L
		self.r = r
		cal = self.np.frompyfunc(self._cal_one_point, 5, 1)
		# compute shells [shell1,shell2,...], shell1=np.array([[x1,y1],[x2,y2],...])
		shell = self.radp.shells_3d([self.r], self.dsize, self.data_center)[0]
		# compute sh
		print("\nCalculating spherical hamonics expansion ...")
		self.Clm = self.np.zeros((self.L, self.L*2+1), dtype=self.np.complex)
		sh_conj = self.np.zeros((self.L, self.L*2+1, len(shell)),dtype=self.np.complex)
		for l in self.np.arange(self.L):
			for m in self.np.arange(-l,l+1,1):
				sh = cal(shell[:,0], shell[:,1], shell[:,2], [m]*len(shell), [l]*len(shell))
				sh_conj[l,m,:] = sh
				self.sys.stdout.write("Processing... " + "l=" + str(l) + ", m=" + str(m)\
				+ ", r=" + str(r) + " \r")
				self.sys.stdout.flush()
		# compute sh des
		delta_omiga = 4*self.np.pi/len(shell)
		sdata = self.data[shell[:,0], shell[:,1], shell[:,2]]
		self.Clm = self.np.sum(sdata*sh_conj*delta_omiga, axis=2)
		self.Cl = self.np.linalg.norm(self.Clm, axis=1)
		print("\ndone.\n")
		return self.Cl

def sp_hamonics(data, r, L=10):
	calculator = _sphere_des()
	calculator.load_data(data)
	shdes = calculator.compute(L+1,r)
	return shdes
