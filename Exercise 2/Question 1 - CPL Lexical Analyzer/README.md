# Question 1: CLA - CPL Lexical Analyzer
The script calculates a list of token from a given CPL file. 
The script produces a new file `<cpl_file>.tok` which contains list of tokens which represents the CPL language.
Every line in the *.tok file has 3 fields (separated by tabs `\t`):
+ The token name
+ The lexeme 
+ Token attributes (optional)

## Usage
In the terminal type:
```
python cla.py <cpl_file>.cpl
```

## Example
Execute the following command:
```
python cla.py example.cpl
```

The expected STDERR should be:
```
Error: Invalid token: '100ffx' in line 22!
Error: Invalid token: 'aaaaabbbbbaaabbba' in line 22!
Nir Moshe, 300307824. Compilation Theory.
```

And the expected `example.tok`:
```
ID	a	a
COMMA	,	
ID	b	b
COLON	:	
FLOAT	float	
SEMICOLON	;	
LEFT_CURLY_BRACKETS	{	
READ	read	
LEFT_PARENTHESIS	(	
ID	a	a
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
READ	read	
LEFT_PARENTHESIS	(	
ID	b	b
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
IF	if	
LEFT_PARENTHESIS	(	
ID	a	a
RELOP	<	<
ID	b	b
RIGHT_PARENTHESIS	)	
WRITE	write	
LEFT_PARENTHESIS	(	
ID	a	a
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
ELSE	else	
WRITE	write	
LEFT_PARENTHESIS	(	
ID	b	b
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
FLOAT	float	
ID	c	c
EQUAL_SIGN	=	
NUM	3.	3.0
SEMICOLON	;	
INT	int	
ID	x	x
EQUAL_SIGN	=	
STATIC_CAST	static_cast	
LEFT_STATIC_CAST_BRACKETS	<	
INT	int	
RIGHT_STATIC_CAST_BRACKETS	>	
LEFT_PARENTHESIS	(	
ID	c	c
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
INT	int	
COMMA	,	
SEMICOLON	;	
IF	if	
LEFT_PARENTHESIS	(	
LEFT_PARENTHESIS	(	
ID	x	x
AND	&&	
NOT	!	
ID	x	x
RIGHT_PARENTHESIS	)	
OR	||	
LEFT_PARENTHESIS	(	
ID	x	x
RELOP	==	==
LEFT_PARENTHESIS	(	
ID	x	x
EQUAL_SIGN	=	
NUM	1	1
RIGHT_PARENTHESIS	)	
RIGHT_PARENTHESIS	)	
RIGHT_PARENTHESIS	)	
LEFT_CURLY_BRACKETS	{	
WRITE	write	
LEFT_PARENTHESIS	(	
NUM	1	1
RIGHT_PARENTHESIS	)	
SEMICOLON	;	
RIGHT_CURLY_BRACKETS	}	
RIGHT_CURLY_BRACKETS	}	
Nir Moshe, 300307824. Compilation Theory.
```

## Author
Nir Moshe, nir.moshe.nm@gmail.com
