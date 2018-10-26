# Question 1 - Flex.

## How to build
### Option 1
In the command line type: `make`

### Option 2
Execute the following commands:
```
flex q1_flex.txt
gcc lex.yy.c -ll -o myflex
```

Then you can execute `myflex`.
 
Example:
```
./myflex input_example.txt
```

And you will get:
```
10 green bottles hanging on the wall
2. 10 green bottles hanging on the wall
And if one green bottle should accidentally fall,
4. There'll be nine green bottles hanging on the wall.
```

## Author
Nir Moshe, nir.moshe.nm@gmail.com 
