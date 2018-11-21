# File: question3_example.py
# Date: 21 - November - 2018
#
# Implementation of a recursive descent parser for the given grammar in Ex3. Q3.
#
# Author: Nir Moshe.

INPUT = "bcbccbaca"


def error(input_position):
	raise Exception("Invalid syntax (position: %d = '%s')." % (input_position, INPUT[input_position]))


def A(input_position):
	if INPUT[input_position] == 'a':
		input_position = input_position + 1
		if INPUT[input_position] == 'c':
			input_position = input_position + 1
			return A(input_position)
		else:
			error(input_position)

	elif INPUT[input_position] == 'b':
		input_position = input_position + 1
		if INPUT[input_position] == 'b':
			input_position = S(input_position)
			return A(input_position)
		else:
			error(input_position)

	elif INPUT[input_position] == 'c':
		input_position = input_position + 1
		if INPUT[input_position] == 'b':
			input_position = input_position + 1
			return S(input_position)
		else:
			error(input_position)

	else:
		error(input_position)


def S(input_position):
	if INPUT[input_position] == "c":
		input_position = input_position + 1
		input_position = A(input_position)
		input_position = B(input_position)
		if INPUT[input_position] == "c":
			return input_position + 1
		else:
			error(input_position)

	elif INPUT[input_position] == 'b' or INPUT[input_position] == 'a':
		input_position = B(input_position)
		if INPUT[input_position] == "a":
			return input_position + 1
		else:
			error(input_position)

	else:
		error(input_position)


def B(input_position):
	if INPUT[input_position] == "b":
		input_position = input_position + 1
		return A(input_position)

	# This is the rule B -> epsilon.
	elif INPUT[input_position] == 'c' or INPUT[input_position] == 'a':
		return input_position

	else:
		error(input_position)


def main():
	try:
		res = S(0)
		if res != len(INPUT):
			print("Invalid word")
		else:
			print("word in language!")

	except IndexError:
		print("word in language!")
	except Exception:
		print("Invalid word")
		

if __name__ == "__main__":
	main()
