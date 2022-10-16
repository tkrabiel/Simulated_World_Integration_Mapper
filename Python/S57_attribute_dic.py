colour_dic = {"['3', '6', '3']":"red_yellow_red","['3', '1', '3']":"red_orange_red","['1', '11','1']":"white_orange_white","['1', '11']":"white_orange","['4', '3', '4']":"green_red_green","['3', '4', '3']":"red_green_red","['1']":"white","['2']":"black","['3']":"red","['4']":"green","['5']":"blue","['6']":"yellow","['7']":"grey","['8']":"brown","['9']":"amber","['10']":"violet","['11']":"orange","['12']":"magenta","['13']":"pink",} #"color#":"color"
boyshp_dic = {'1':'nun','2':'can','3':'spherical','4':'pillar','5':'spar','6':'tun','7':'super_buoy','8':'ice_buoy'} #"shape#":"shape"
catcam_dic = {'1':'north','2':'east','3':'south','4':'west'}#'cat#':'direction'



#x<0.2 = Nothing 0.2>x>0.3 = L  0.6>x>0.3 = LL 0.6>x>0.8 = LLL 0.8>x>=1 = LLLL
#could do a count? formula for 1.3/0.25 = round(3.2) LLLLL 1.7/0.25 = round(6.8) DDDDDDDD
#while x > 0:
#string to num
#sting[1:-1]
#if z[1] = '('
    #x = float(x[1:-1])
#x = ('(1.3)')
#x[1:-1]
#x = round(4.6)
#d = []
#while x>0:
    #d.append("L")
    #x -= 0.25
#out = "".join(d)
#x -= 1
# L,D = 0.25 seconds D = dark L = Light 0.3+(0.7) = LDDD  1.3+(1.7) = LLLLLDDDDDDD


#color
#1,white 2,black 3,red 4,green 5,blue 6,yello 7,grey 8,brown 9,amber 10,violet 11,orange 12,magenta 13,pink

#becon shape BCNSHP for BCNLAT
#1,pole 2,withy 3,beacon tower 4,lattice 5,pile 6,cairn 7,buoyant

#boyspp and bcnspp
#1, firing 2,target 3,markership 4,degaussing 5,barge 6,cable, 7, spoil