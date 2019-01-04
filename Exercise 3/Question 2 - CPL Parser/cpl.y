start: declarations stmt_block

declarations: declarations declaration
              | epsilon

declaration: idlist COLON type SEMICOLON

type: INT | FLOAT

idlist: idlist COMMA ID | ID

stmt: assignment_stmt
      | input_stmt
      | output_stmt
      | cast_stmt
      | if_stmt
      | while_stmt
      | switch_stmt
      | break_stmt
      | continue_stmt
      | stmt_block

assignment_stmt: ID EQUAL_SIGN expression SEMICOLON

input_stmt: READ LEFT_PARENTHESIS ID RIGHT_PARENTHESIS SEMICOLON

output_stmt: WRITE LEFT_PARENTHESIS expression RIGHT_PARENTHESIS SEMICOLON

cast_stmt: ID EQUAL_SIGN STATIC_CAST LEFT_STATIC_CAST_BRACKETS type RIGHT_STATIC_CAST_BRACKETS LEFT_PARENTHESIS expression RIGHT_PARENTHESIS SEMICOLON

if_stmt: IF LEFT_PARENTHESIS boolexpr RIGHT_PARENTHESIS stmt ELSE stmt

while_stmt: WHILE LEFT_PARENTHESIS boolexpr RIGHT_PARENTHESIS stmt

switch_stmt: SWITCH LEFT_PARENTHESIS expression RIGHT_PARENTHESIS LEFT_CURLY_BRACKETS caselist DEFAULT COLON stmtlist RIGHT_CURLY_BRACKETS

caselist: caselist CASE NUM COLON stmtlist SEMICOLON
          | epsilon

break_stmt: BREAK SEMICOLON

continue_stmt: CONTINUE SEMICOLON

stmt_block: LEFT_CURLY_BRACKETS stmtlist RIGHT_CURLY_BRACKETS

stmtlist: stmtlist stmt | epsilon

boolexpr: boolexpr OR boolterm
          | boolterm

boolterm: boolterm AND boolfactor
          | boolfactor

boolfactor: NOT LEFT_PARENTHESIS boolexpr RIGHT_PARENTHESIS
            | expression RELOP expression

expression: expression ADDOP term
            | term

term: term MULOP factor
      | factor

factor: LEFT_PARENTHESIS expression RIGHT_PARENTHESIS
        | ID
        | NUM

epsilon:
%declare COLON SEMICOLON INT FLOAT ID COMMA EQUAL_SIGN LEFT_PARENTHESIS RIGHT_PARENTHESIS LEFT_CURLY_BRACKETS
%declare RIGHT_CURLY_BRACKETS LEFT_STATIC_CAST_BRACKETS RIGHT_STATIC_CAST_BRACKETS NUM ADDOP MULOP RELOP AND OR NOT
%declare CONTINUE BREAK IF ELSE WHILE SWITCH CASE DEFAULT READ WRITE STATIC_CAST
