import random

from PIL import Image, ImageDraw, ImageFont

from .enums import Teams, TileStates
    
    
def get_random_words(count, not_containing=list()):
    with open('words.txt', 'r') as word_file:
        words = word_file.read().split('\n')
    for word in not_containing:
        try: words.remove(word)
        except ValueError: pass
    words = random.sample(words, count)
    return words


class Board:

    def __init__(self, width=5, height=5, words=list()):
        self.width = width
        self.height = height
        self.winner = None
        self.turn = Teams.RED
        self.notturn = Teams.BLUE
        self.move_count = 0
        self.max_moves = 0
        self._board = [[None for i in range(height)] for j in range(width)]
        self.words = list(words) + get_random_words(max(0,width*height-len(words)), not_containing=words)
        random.shuffle(self.words)
        i = 0
        tiles = {(x, y) for x in range(height) for y in range(width)}
        states = {}
        for ts in TileStates.__members__.values():
            if ts.count:
                chosen = random.sample(tiles, ts.count)
                for c in chosen:
                    states[c] = ts
                    tiles -= set(chosen)
                    
        for remaining in tiles:
            states[remaining] = TileStates.BYSTANDER
        
        for x in range(len(self._board)):
            for y in range(len(self._board[x])):
                self._board[x][y] = Tile(self.words[i], states[(x, y)])
                i += 1
                
    def get_word(self, word):
        for x in range(len(self._board)):
            for y in range(len(self._board[x])):
                if self._board[x][y].word.lower() == word.lower():
                    return (x, y)
        raise IndexError
    
    def get_winner(self):
        return self.winner
    
    def switch_turn(self):
        self.move_count = 0
        self.max_moves = 0
        self.turn, self.notturn = self.notturn, self.turn
        
    def do_move(self, word):
        if self.max_moves == 0: return -1
        try: result = self.uncover(*self.get_word(word))
        except IndexError: return -1
        self.move_count += 1
        if result == -1: 
            self.switch_turn()
            self.winner = self.notturn
        elif result == 1: self.switch_turn()
        elif self.move_count >= self.max_moves: self.switch_turn()
        return self.check_winner()
        
    def check_winner(self):
        red_win = True
        blue_win = True
        for col in self._board:
            for tile in col:
                if not tile.uncovered:
                    if tile.state == TileStates.RED:
                        red_win = False
                    elif tile.state == TileStates.BLUE:
                        blue_win = False

        if red_win: self.winner = Teams.RED
        elif blue_win: self.winner = Teams.BLUE
        return self.winner
        
    def set_hint_number(self, num):
        self.max_moves = num+1
    
    def uncover(self, x, y):
        team = self._board[x][y].uncover()
        if team.value[0] == self.turn: return 0
        elif team == TileStates.ASSASSIN: return -1
        else: return 1
    
    def get_tile_at(self, x, y):
        return self._board[x][y]
    
    def draw(self, unhidden=False):
        img = Image.new('RGB', (100*self.width,100*self.height), color=(255,255,255))
        for x in range(self.width):
            for y in range(self.height):
                cell = self._board[x][y].draw(unhidden=unhidden)
                img.paste(cell, box=(x*100,y*100))
                
        return img
    
class Tile:
    def __init__(self, word, state):
        self.word = word
        self.state = state
        self.uncovered = False
        
    def uncover(self):
        self.uncovered = True
        return self.state
    
    def draw(self, unhidden=False):
        img = Image.new('RGB', (100,100), color=(255,255,255))
        drawer = ImageDraw.Draw(img)
        color = None
        if unhidden or self.uncovered:
            if self.state == TileStates.RED: color = (216, 108, 112)
            elif self.state == TileStates.BLUE: color = (112, 108, 216)
            elif self.state == TileStates.BYSTANDER: color = (239,224,96)
            elif self.state == TileStates.ASSASSIN: color = (128,128,128)
        else:
            color = (255,255,255)
        drawer.rectangle([0,0,100,100], fill=color, outline=(0,0,0))
        arial = ImageFont.truetype('./arial.ttf', size=14)
        text = wrap_text(self.word, 90, arial, drawer)
        w, h = drawer.textsize(text, font=arial)
        drawer.multiline_text((50-w/2,50-h/2), text, font=arial, fill=(0,0,0), align='center')
        return img
    
def wrap_text(text,width,font,drawer):
    
    text_list = [text]
    
    while drawer.textsize(text_list[-1],font)[0] > width:
        nearest_space = get_nearest_space(text_list[-1],width,font,drawer)
        first = text_list[-1][:nearest_space]
        second = text_list[-1][nearest_space:]
        text_list[-1] = first
        text_list.append(second)
        
    return '\n'.join(text_list)
        
    
    
def get_nearest_space(text,width,font,drawer):
    text = text.replace('_',' ')
    text_width = drawer.textsize(text,font)[0]
    
    if width > text_width:
        return len(text)
    
    guess = len(text)*width // text_width
    
    while drawer.textsize(text[:guess],font)[0] < width:
        guess +=1
        
    while drawer.textsize(text[:guess],font)[0] > width:
        guess -= 1
        
    char_num = guess
    
    while char_num > 0:
        if text[char_num] in '- _':
            return char_num+1
        char_num -= 1
        
    return guess
    
        
if __name__ == '__main__':
    board = Board()
    img = board.draw(True)
    img.save('text.png')
    
        

