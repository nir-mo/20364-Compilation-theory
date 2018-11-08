# Exercise 1 Question 1 Flex Makefile
# Nir Moshe

myflex: lex.yy.c
	gcc lex.yy.c -ll -o myflex

lex.yy.c: q1_flex.txt
	flex q1_flex.txt

clean:
	rm lex.yy.c myflex