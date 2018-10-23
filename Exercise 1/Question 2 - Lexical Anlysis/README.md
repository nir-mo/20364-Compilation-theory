# Question2: Playlist lexical analyzer

## Tokens
In order to tokenize a playlist I defined the following tokens, which represents the basic blocks in 
the playlist grammar.
 + `PLAYLIST` - represents `[playlist]` keyword.
 + `SONG` - represents `[song]` keyword.
 + `LENGTH` - represents `[length]` keyword.
 + `ARTIST` - represents `[artist]` keyword.
 + `NUMBER` - represents any integer (example: 5).
 + `STRING` - represents an arbitrary sequence of characters: letter, number, underscore + any of the characters: ! # - & ' WITHOUT whitespaces.
 + `QUOTED_STRING` - represents a string with quotes (example: "Hello world") it may contain white space ( ) and tab (\t).
 + `DURATION` - represents a string with the pattern `\d+:[0-5]{1}\d{1}` (example: '3:45').

Note that the tokenizer ignores white spaces (except for `QUOTED_STRING`).

## Usage
In the command line, execute:
```
python songs.py <file_name>
```

You can try it on the files `invalid_playlist.txt` and `valid_playlist.txt` (see the example).

## Examples
Execute:
```
 python songs.py valid_playlist.txt 
```

Output:
```
TOKEN         LEXEME        ATTRIBUTE   

PLAYLIST      [playlist]                
NUMBER        1             1           
SONG          [song]                    
QUOTED_STRING  "Hello baby"  Hello baby  
ARTIST        [artist]                  
STRING        nirmo                     
STRING        &                         
STRING        friends                   
LENGTH        [length]                  
DURATION      1:11                      
NUMBER        2             2           
SONG          [song]                    
QUOTED_STRING  "Ma [song] #7"  Ma [song] #7
ARTIST        [artist]                  
STRING        1st                       
STRING        dude!                     
LENGTH        [length]                  
DURATION      77:17                     
NUMBER        3             3           
SONG          [song]                    
QUOTED_STRING  "Nothing else matters"  Nothing else matters
ARTIST        [artist]                  
STRING        Metallica                 
LENGTH        [length]                  
DURATION      3:33                      
```
