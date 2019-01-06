"""
############
Slider
############
.. module:: Slider

"""


MAX_INT = 2147483647
MIN_INT = -2147483648

class Slider(object):
	'''
	Slider object allows us to convert Boolean values to numeric values.
	By passing a slider as an argument to a function instead of a bool var we can determine how crucial the argument is for the next move.
	And can calculate more easily the best move for the character.
	'''

	MIN_LIM = 0
	MAX_LIM = 1

	def __init__(self, value=0, boundaries=(MIN_INT , MAX_INT)):
		'''
		value is the corrent value of the slider while boundaries are the maximum and minmum values "value" can be.
		'''
		self.value = float(value)
		self.boundaries = boundaries


	def __get_in_limit(self, num):
		'''
		returns the number if it in the limits else returns the corrsponding limit
		'''
		if num >= 0: #if the number is positiv
			return min(num, self.boundaries[self.MAX_LIM])#return the smallst number betwen the num and the max limit
		return max(num, self.boundaries[self.MIN_LIM])
	

	#four mathmatical opertions:
	#---------------------------
	def __add__(self, other):
		'''
		x + y where type(x) is Slider
		'''
		#print isinstance(other, Slider)
		sum1 = self.value
		if isinstance(other, Slider):
			sum1 += other.value
		else:
			sum1 += other

		return self.__get_in_limit(sum1)


	def __radd__(self, other):
		'''
		y + x where type(x) is Slider
		'''
		return self.__add__(other)

	
	def __iadd__(self, other):
		'''
		x += y where type(x) is Slider
		'''
		self.value = self + other
		return self


	def __sub__(self, other):
		'''
		x - y where type(x) is Slider
		'''
		sum1 = self.value
		if isinstance(other, Slider):
			sum1 -= other.value
		else:
			sum1 -= other

		return self.__get_in_limit(sum1)
		

	def __rsub__(self, other):
			'''
			y - x where type(x) is Slider
			'''
			return other - self.value


	def __isub__(self, other):
		'''
		x -= y where type(x) is Slider
		'''
		self.value = self - other
		return self

	
	def __mul__(self, other):
		'''
		x * y where type(x) is Slider
		'''
		sum1 = self.value
		if isinstance(other, Slider):
			sum1 *= other.value
		else:
			sum1 *= other

		return self.__get_in_limit(sum1)


	def __rmul__(self, other):
		'''
		y * x where type(x) is Slider
		'''
		return self * other
	

	def __imul__(self, other):
		'''
		x *= y where type(x) is Slider
		'''
		self.value = self * other
		return self


	def __div__(self, other):
		'''
		x / y where type(x) is Slider
		'''
		sum1 = self.value
		if isinstance(other, Slider):
			sum1 /= other.value
		else:
			sum1 /= other

		return self.__get_in_limit(sum1)


	def __rdiv__(self, other):
		'''
		y / x where type(x) is Slider
		'''
		return other / self.value 


	def __idiv__(self, other):
		'''
		x /= y where type(x) is Slider
		'''
		self.value = self / other
		return self

	#Comparison magic methods:
	#-------------------------

	def __nonzero__(self):
		return self.value != 0

	def __eq__(self, other):
		return self.value == other.value and self.boundaries == other.boundaries

	def __cmp__(self, other):
		return self.value - other.value

	#conversions:
	#------------

	def __int__(self):
		return int(self.value)

	def __float__(self):
		return self.value

	def __str__(self):
		return "Slider value: %s, slider limit: %s" %(str(self.value), str(self.boundaries))



def main():
	s = Slider(0, (0, 100))
	
	if s:
		print s


if __name__ == '__main__':
	main()