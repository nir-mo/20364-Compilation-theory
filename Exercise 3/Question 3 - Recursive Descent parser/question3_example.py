# File: question3_example.py
# Date: 21 - November - 2018
#
# Implementation of a recursive descent parser for the given grammar in Ex3. Q3.
#
# Author: Nir Moshe.

INPUT = "bcbccbaca"
input_position = 0


def error():
	raise Exception("Invalid syntax (position: %d = '%s')." % (input_position, lookahead()))


def match(token):
	global input_position
	if lookahead() == token:
		input_position += 1
	else:
		error()


def lookahead():
	return INPUT[input_position]


def A():
	if lookahead() == 'a':
		match("a")
		match("c")
		A()

	elif lookahead() == 'b':
		match('b')
		match('b')
		S()
		A()

	elif lookahead() == 'c':
		match('c')
		match('b')
		S()

	else:
		error()


def S():
	if lookahead() == "c":
		match('c')
		A()
		B()
		match("c")

	elif lookahead() in ('a', 'b'):
		B()
		match("a")

	else:
		error()


def B():
	if lookahead() == "b":
		match("b")
		A()

	# This is the rule B -> epsilon.
	elif lookahead() in ('a', 'c'):
		pass

	else:
		error()


def main():
	try:
		S()
		if input_position != len(INPUT):
			print("Invalid word")
		else:
			print("word in language!")

	except IndexError:
		print("word in language!")
	except Exception:
		print("Invalid word")
		

if __name__ == "__main__":
	main()
