'''
a module to make it easy to get some test data

NOTE: all methods that return strings will return unicode strings

for a utf-8 stress test, see: http://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
'''
import re
import random
import string
import sys

def get_url():
    '''
    get a url, this is just a nice shortcut method to something I seemed to do a lot
    
    return -- unicode
    '''
    return u'http{}://{}.com'.format(
        u's' if random.choice([True, False]) else u'',
        get_ascii()
    )
     
def get_str(str_size=0, chars=None):
    '''
    generate a random unicode string
    
    str_size -- integer -- how long you want the string to be
    chars -- sequence -- the characters you want the string to use, if this is None, it
        will default to pretty much the entire unicode range of characters
    return -- unicode
    '''
    if str_size == 0:
        str_size = random.randint(3, 20)

    sg = None

    if chars is None:
        # chars can be any range in unicode
        # via: http://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
        byte_range = lambda first, last: range(first, last+1)
        first_values = byte_range(0x00, 0x7F) + byte_range(0xC2, 0xF4)
        trailing_values = byte_range(0x80, 0xBF)

        def random_utf8_seq():
            first = random.choice(first_values)
            if first <= 0x7F:
                return bytearray([first])
            elif first <= 0xDF:
                return bytearray([first, random.choice(trailing_values)])
            elif first == 0xE0:
                return bytearray([first, random.choice(byte_range(0xA0, 0xBF)), random.choice(trailing_values)])
            elif first == 0xED:
                return bytearray([first, random.choice(byte_range(0x80, 0x9F)), random.choice(trailing_values)])
            elif first <= 0xEF:
                return bytearray([first, random.choice(trailing_values), random.choice(trailing_values)])
            elif first == 0xF0:
                return bytearray(
                    [first, random.choice(byte_range(0x90, 0xBF)), random.choice(trailing_values), random.choice(trailing_values)]
                )
            elif first <= 0xF3:
                return bytearray([first, random.choice(trailing_values), random.choice(trailing_values), random.choice(trailing_values)])
            elif first == 0xF4:
                return bytearray(
                    [first, random.choice(byte_range(0x80, 0x8F)), random.choice(trailing_values), random.choice(trailing_values)]
                )

        sg = (random_utf8_seq().decode('utf-8') for c in xrange(str_size))

    else:
        # we have a defined set of chars
        sg = (random.choice(chars) for c in xrange(str_size))

    s = u''.join(sg)
    return s

def get_ascii(str_size=0):
    '''
    generate a random string full of just ascii characters
    
    str_size -- integer -- how long you want the string to be
    return -- unicode
    '''
    chars=string.ascii_letters + string.digits
    return get_str(str_size, chars)

def get_float(min_size=None, max_size=None):
    '''
    get a random float

    no different than random.uniform() except it automatically can set range, and
    guarrantees that no 2 floats are the same
    
    return -- float
    '''
    float_info = sys.float_info
    if min_size is None:
        min_size = float_info.min
    if max_size is None:
        max_size = float_info.max

    i = 0;
    
    while True:
        i = random.uniform(min_size, max_size)
        if i not in _previous_floats:
            _previous_floats.add(i)
            break
    
    return i

def get_int(min_size=1, max_size=sys.maxsize):
    '''
    get a random integer

    no different than random.randint except that it guarrantees no int will be
    the same, and also you don't have to set a range, it will default to all max
    int size
    
    return -- integer 
    '''
    i = 0;
    
    while True:
        i = random.randint(min_size, max_size)
        if i not in _previous_ints:
            _previous_ints.add(i)
            break
    
    return i

def get_words(word_count=0, as_str=True):
    '''
    get some amount of random words

    word_count -- integer -- how many words you want, 0 means a random amount (at most 20)
    as_str -- boolean -- True to return as string, false to return as list of words

    return -- unicode|list -- your requested words
    '''

    # since we specified we didn't care, randomly choose how many surnames there should be
    if word_count == 0:
        word_count = random.randint(1, 20)

    words = random.sample(_words, word_count)
    return words if not as_str else u' '.join(words)

def get_name(name_count=2, as_str=True):
    '''
    get a random name

    link -- http://stackoverflow.com/questions/30485/what-is-a-reasonable-length-limit-on-person-name-fields

    name_count -- integer -- how many total name parts you want (eg, "Jay marcyes" = 2 name_count)
    as_str -- boolean -- True to return as string, false to return as list of names

    return -- unicode|list -- your requested name
    '''

    # since we specified we didn't care, randomly choose how many surnames there should be
    if name_count == 0:
        name_count = random.randint(1, 5)

    names = random.sample(_names, name_count)
    return names if not as_str else u' '.join(names)

def get_coordinate(v1, v2, round_to=7):
    '''
    this will get a random coordinate between the values v1 and v2

    handy for doing geo stuff where you want to make sure you have a coordinate within
    N miles of a central coordinate so you can make your tests repeatable

    v1 -- float -- the first coordinate
    v2 -- float -- the second coordinate

    return -- float -- a value between v1 and v2
    '''
    v1 = [int(x) for x in str(round(v1, round_to)).split('.')]
    v2 = [int(x) for x in str(round(v2, round_to)).split('.')]
    scale_max = int('9' * round_to)
    
    min = v1
    max = v2
    if v1[0] > v2[0]:
      min = v2
      max = v1
    
    min_size = min[0]
    min_scale_range = [min[1], scale_max]
    
    max_size = max[0]
    max_scale_range = [0, max[1]]
    
    scale = 0
    size = random.randint(min_size, max_size)

    
    if size == min_size:
      scale = random.randint(min_scale_range[0], min_scale_range[1])
    elif size == max_size:
        # if you get a random value from 0 to say 23456, you might get 9070, which is
        # less than 23456, but when put into a float it would be: N.9070, which is bigger
        # than the passed in v2 float, the following code avoids that problem
        left_zero_count = random.randint(0, round_to)
        if left_zero_count == round_to:
            scale = '0' * round_to
        elif left_zero_count > 0:
            scale = int(str(scale_max)[left_zero_count:])
            scale = str(random.randint(max_scale_range[0], scale)).zfill(round_to)
        else:
            scale = random.randint(int('1' + ('0' * (round_to - 1))), max_scale_range[1])
    else:
      scale = random.randint(0, scale_max)
  
    return float('{}.{}'.format(size, scale))


# used in the get_int() method to make sure it never returns the same int twice
# this is a possible memory leak if you are using this script in a very long running
# process using get_int(), since this list will get bigger and bigger and never
# be flushed, but seriously, you should just use random.randint() in any long running
# scripts
_previous_ints = set()

# similar to get_int()
_previous_floats = set()

# all the names to choose from in get_name()
# TODO: add utf names outside ascii range
_names = re.split(r'\s+', u'''
mary patricia linda barbara elizabeth jennifer maria susan margaret dorothy lisa nancy karen betty helen
sandra donna carol ruth sharon michelle laura sarah kimberly deborah jessica shirley cynthia angela
melissa brenda amy anna rebecca virginia kathleen pamela martha debra amanda stephanie carolyn
christine marie janet catherine frances ann joyce diane alice julie heather teresa doris gloria
evelyn jean cheryl mildred katherine joan ashley judith rose janice kelly nicole judy christina
kathy theresa beverly denise tammy irene jane lori rachel marilyn andrea kathryn louise sara anne
jacqueline wanda bonnie julia ruby lois tina phyllis norma paula diana annie lillian emily robin
peggy crystal gladys rita dawn connie florence tracy edna tiffany carmen rosa cindy grace wendy
victoria edith kim sherry sylvia josephine thelma shannon sheila ethel ellen elaine marjorie carrie
charlotte monica esther pauline emma juanita anita rhonda hazel amber eva debbie april leslie clara
lucille jamie joanne eleanor valerie danielle megan alicia suzanne michele gail bertha darlene veronica
jill erin geraldine lauren cathy joann lorraine lynn sally regina erica beatrice dolores bernice
audrey yvonne annette june samantha marion dana stacy ana renee ida vivian roberta holly brittany
melanie loretta yolanda jeanette laurie katie kristen vanessa alma sue elsie beth jeanne vicki carla
tara rosemary eileen terri gertrude lucy tonya ella stacey wilma gina kristin jessie natalie agnes vera
willie charlene bessie delores melinda pearl arlene maureen colleen allison tamara joy georgia constance
lillie claudia jackie marcia tanya nellie minnie marlene heidi glenda lydia viola courtney marian stella
caroline dora jo vickie mattie terry maxine irma mabel marsha myrtle lena christy deanna patsy hilda
gwendolyn jennie nora margie nina cassandra leah penny kay priscilla naomi carole brandy olga billie
dianne tracey leona jenny felicia sonia miriam velma becky bobbie violet kristina toni misty mae shelly
daisy ramona sherri erika katrina claire lindsey lindsay geneva guadalupe belinda margarita sheryl cora
faye ada natasha sabrina isabel marguerite hattie harriet molly cecilia kristi brandi blanche sandy
rosie joanna iris eunice angie inez lynda madeline amelia alberta genevieve monique jodi janie maggie
kayla sonya jan lee kristine candace fannie maryann opal alison yvette melody luz susie olivia flora
shelley kristy mamie lula lola verna beulah antoinette candice juana jeannette pam kelli hannah whitney
bridget karla celia latoya patty shelia gayle della vicky lynne sheri marianne kara jacquelyn erma blanca
myra leticia pat krista roxanne angelica johnnie robyn francis adrienne rosalie alexandra brooke bethany
sadie bernadette traci jody kendra jasmine nichole rachael chelsea mable ernestine muriel marcella elena
krystal angelina nadine kari estelle dianna paulette lora mona doreen rosemarie angel desiree antonia
hope ginger janis betsy christie freda mercedes meredith lynette teri cristina eula leigh meghan sophia
eloise rochelle gretchen cecelia raquel henrietta alyssa jana kelley gwen kerry jenna tricia laverne
olive alexis tasha silvia elvira casey delia sophie kate patti lorena kellie sonja lila lana darla may
mindy essie mandy lorene elsa josefina jeannie miranda dixie lucia marta faith lela johanna shari camille
tami shawna elisa ebony melba ora nettie tabitha ollie jaime winifred kristie marina alisha aimee rena
myrna marla tammie latasha bonita patrice ronda sherrie addie francine deloris stacie adriana cheri shelby
abigail celeste jewel cara adele rebekah lucinda dorthy chris effie trina reba shawn sallie aurora lenora
etta lottie kerri trisha nikki estella francisca josie tracie marissa karin brittney janelle lourdes
laurel helene fern elva corinne kelsey ina bettie elisabeth aida caitlin ingrid iva eugenia christa
goldie cassie maude jenifer therese frankie dena lorna janette latonya candy morgan consuelo tamika
rosetta debora cherie polly dina jewell fay jillian dorothea nell trudy esperanza patrica kimberley shanna
helena carolina cleo stefanie rosario ola janine mollie lupe alisa lou maribel susanne bette susana elise
cecile isabelle lesley jocelyn paige joni rachelle leola daphne alta ester petra graciela imogene jolene
keisha lacey glenna gabriela keri ursula lizzie kirsten shana adeline mayra jayne jaclyn gracie sondra
carmela marisa rosalind charity tonia beatriz marisol clarice jeanine sheena angeline frieda lily robbie
shauna millie claudette cathleen angelia gabrielle autumn katharine summer jodie staci lea christi jimmie
justine elma luella margret dominique socorro rene martina margo mavis callie bobbi maritza lucile leanne
jeannine deana aileen lorie ladonna willa manuela gale selma dolly sybil abby lara dale ivy dee winnie
marcy luisa jeri magdalena ofelia meagan audra matilda leila cornelia bianca simone bettye randi virgie
latisha barbra georgina eliza leann bridgette rhoda haley adela nola bernadine flossie ila greta ruthie
nelda minerva lilly terrie letha hilary estela valarie brianna rosalyn earline catalina ava mia clarissa
lidia corrine alexandria concepcion tia sharron rae dona ericka jami elnora chandra lenore neva marylou
melisa tabatha serena avis allie sofia jeanie odessa nannie harriett loraine penelope milagros emilia
benita allyson ashlee tania tommie esmeralda karina eve pearlie zelma malinda noreen tameka saundra hillary
amie althea rosalinda jordan lilia alana gay clare alejandra elinor michael lorrie jerri darcy earnestine
carmella taylor noemi marcie liza annabelle louisa earlene mallory carlene nita selena tanisha katy julianne
john lakisha edwina maricela margery kenya dollie roxie roslyn kathrine nanette charmaine lavonne ilene
kris tammi suzette corine kaye jerry merle chrystal lina deanne lilian juliana aline luann kasey maryanne
evangeline colette melva lawanda yesenia nadia madge kathie eddie ophelia valeria nona mitzi mari georgette
claudine fran alissa roseann lakeisha susanna reva deidre chasity sheree carly james elvia alyce deirdre
gena briana araceli katelyn rosanne wendi tessa berta marva imelda marietta marci leonor arline sasha
madelyn janna juliette deena aurelia josefa augusta liliana young christian lessie amalia savannah
anastasia vilma natalia rosella lynnette corina alfreda leanna carey amparo coleen tamra aisha wilda
karyn cherry queen maura mai evangelina rosanna hallie erna enid mariana lacy juliet jacklyn freida
madeleine mara hester cathryn lelia casandra bridgett angelita jannie dionne annmarie katina beryl phoebe
millicent katheryn diann carissa maryellen liz lauri helga gilda adrian rhea marquita hollie tisha tamera
angelique francesca britney kaitlin lolita florine rowena reyna twila fanny janell ines concetta bertie
alba brigitte alyson vonda pansy elba noelle letitia kitty deann brandie louella leta felecia sharlene
lesa beverley robert isabella herminia terra celina

aaron abdul abe abel abraham abram adalberto adam adan adolfo adolph adrian agustin ahmad ahmed al alan
albert alberto alden aldo alec alejandro alex alexander alexis alfonso alfonzo alfred alfredo ali allan
allen alonso alonzo alphonse alphonso alton alva alvaro alvin amado ambrose amos anderson andre andrea
andreas andres andrew andy angel angelo anibal anthony antione antoine anton antone antonia antonio
antony antwan archie arden ariel arlen arlie armand armando arnold arnoldo arnulfo aron arron art arthur
arturo asa ashley aubrey august augustine augustus aurelio austin avery barney barrett barry bart barton
basil beau ben benedict benito benjamin bennett bennie benny benton bernard bernardo bernie berry bert
bertram bill billie billy blaine blair blake bo bob bobbie bobby booker boris boyce boyd brad bradford
bradley bradly brady brain branden brandon brant brendan brendon brent brenton bret brett brian brice
britt brock broderick brooks bruce bruno bryan bryant bryce bryon buck bud buddy buford burl burt burton
buster byron caleb calvin cameron carey carl carlo carlos carlton carmelo carmen carmine carol carrol
carroll carson carter cary casey cecil cedric cedrick cesar chad chadwick chance chang charles charley
charlie chas chase chauncey chester chet chi chong chris christian christoper christopher chuck chung
clair clarence clark claud claude claudio clay clayton clement clemente cleo cletus cleveland cliff
clifford clifton clint clinton clyde cody colby cole coleman colin collin colton columbus connie conrad
cordell corey cornelius cornell cortez cory courtney coy craig cristobal cristopher cruz curt curtis
cyril cyrus dale dallas dalton damian damien damion damon dan dana dane danial daniel danilo dannie danny
dante darell daren darin dario darius darnell daron darrel darrell darren darrick darrin darron darryl
darwin daryl dave david davis dean deandre deangelo dee del delbert delmar delmer demarcus demetrius denis
dennis denny denver deon derek derick derrick deshawn desmond devin devon dewayne dewey dewitt dexter
dick diego dillon dino dion dirk domenic domingo dominic dominick dominique don donald dong donn donnell
donnie donny donovan donte dorian dorsey doug douglas douglass doyle drew duane dudley duncan dustin
dusty dwain dwayne dwight dylan earl earle earnest ed eddie eddy edgar edgardo edison edmond edmund
edmundo eduardo edward edwardo edwin efrain efren elbert elden eldon eldridge eli elias elijah eliseo
elisha elliot elliott ellis ellsworth elmer elmo eloy elroy elton elvin elvis elwood emanuel emerson
emery emil emile emilio emmanuel emmett emmitt emory enoch enrique erasmo eric erich erick erik erin
ernest ernesto ernie errol ervin erwin esteban ethan eugene eugenio eusebio evan everett everette ezekiel
ezequiel ezra fabian faustino fausto federico felipe felix felton ferdinand fermin fernando fidel filiberto
fletcher florencio florentino floyd forest forrest foster frances francesco francis francisco frank
frankie franklin franklyn fred freddie freddy frederic frederick fredric fredrick freeman fritz gabriel
gail gale galen garfield garland garret garrett garry garth gary gaston gavin gayle gaylord genaro gene
geoffrey george gerald geraldo gerard gerardo german gerry gil gilbert gilberto gino giovanni giuseppe
glen glenn gonzalo gordon grady graham graig grant granville greg gregg gregorio gregory grover guadalupe
guillermo gus gustavo guy hai hal hank hans harlan harland harley harold harris harrison harry harvey
hassan hayden haywood heath hector henry herb herbert heriberto herman herschel hershel hilario hilton
hipolito hiram hobert hollis homer hong horace horacio hosea houston howard hoyt hubert huey hugh hugo
humberto hung hunter hyman ian ignacio ike ira irvin irving irwin isaac isaiah isaias isiah isidro ismael
israel isreal issac ivan ivory jacinto jack jackie jackson jacob jacques jae jaime jake jamaal jamal jamar
jame jamel james jamey jamie jamison jan jared jarod jarred jarrett jarrod jarvis jason jasper javier jay
jayson jc jean jed jeff jefferey jefferson jeffery jeffrey jeffry jerald jeramy jere jeremiah jeremy
jermaine jerold jerome jeromy jerrell jerrod jerrold jerry jess jesse jessie jesus jewel jewell jim jimmie
jimmy joan joaquin jody joe joel joesph joey john johnathan johnathon johnie johnnie johnny johnson jon
jonah jonas jonathan jonathon jordan jordon jorge jose josef joseph josh joshua josiah jospeh josue juan
jude judson jules julian julio julius junior justin kareem karl kasey keenan keith kelley kelly kelvin
ken kendall kendrick keneth kenneth kennith kenny kent kenton kermit kerry keven kevin kieth kim king kip
kirby kirk korey kory kraig kris kristofer kristopher kurt kurtis kyle lacy lamar lamont lance landon lane
lanny larry lauren laurence lavern laverne lawerence lawrence lazaro leandro lee leif leigh leland lemuel
len lenard lenny leo leon leonard leonardo leonel leopoldo leroy les lesley leslie lester levi lewis
lincoln lindsay lindsey lino linwood lionel lloyd logan lon long lonnie lonny loren lorenzo lou louie
louis lowell loyd lucas luciano lucien lucio lucius luigi luis luke lupe luther lyle lyman lyndon lynn
lynwood mac mack major malcolm malcom malik man manual manuel marc marcel marcelino marcellus marcelo
marco marcos marcus margarito maria mariano mario marion mark markus marlin marlon marquis marshall
martin marty marvin mary mason mathew matt matthew maurice mauricio mauro max maximo maxwell maynard
mckinley mel melvin merle merlin merrill mervin micah michael michal michale micheal michel mickey miguel
mike mikel milan miles milford millard milo milton minh miquel mitch mitchel mitchell modesto mohamed
mohammad mohammed moises monroe monte monty morgan morris morton mose moses moshe murray myles myron
napoleon nathan nathanael nathanial nathaniel neal ned neil nelson nestor neville newton nicholas nick
nickolas nicky nicolas nigel noah noble noe noel nolan norbert norberto norman normand norris numbers
octavio odell odis olen olin oliver ollie omar omer oren orlando orval orville oscar osvaldo oswaldo
otha otis otto owen pablo palmer paris parker pasquale pat patricia patrick paul pedro percy perry pete
peter phil philip phillip pierre porfirio porter preston prince quentin quincy quinn quintin quinton
rafael raleigh ralph ramiro ramon randal randall randell randolph randy raphael rashad raul ray rayford
raymon raymond raymundo reed refugio reggie reginald reid reinaldo renaldo renato rene reuben rex rey
reyes reynaldo rhett ricardo rich richard richie rick rickey rickie ricky rico rigoberto riley rob robbie
robby robert roberto robin robt rocco rocky rod roderick rodger rodney rodolfo rodrick rodrigo rogelio
roger roland rolando rolf rolland roman romeo ron ronald ronnie ronny roosevelt rory rosario roscoe rosendo
ross roy royal royce ruben rubin rudolf rudolph rudy rueben rufus rupert russ russel russell rusty ryan
sal salvador salvatore sam sammie sammy samual samuel sandy sanford sang santiago santo santos saul scot
scott scottie scotty sean sebastian sergio seth seymour shad shane shannon shaun shawn shayne shelby
sheldon shelton sherman sherwood shirley shon sid sidney silas simon sol solomon son sonny spencer stacey
stacy stan stanford stanley stanton stefan stephan stephen sterling steve steven stevie stewart stuart
sung sydney sylvester tad tanner taylor ted teddy teodoro terence terrance terrell terrence terry thad
thaddeus thanh theo theodore theron thomas thurman tim timmy timothy titus tobias toby tod todd tom tomas
tommie tommy toney tony tory tracey tracy travis trent trenton trevor trey trinidad tristan troy truman
tuan ty tyler tyree tyrell tyron tyrone tyson ulysses val valentin valentine van vance vaughn vern vernon
vicente victor vince vincent vincenzo virgil virgilio vito von wade waldo walker wallace wally walter
walton ward warner warren waylon wayne weldon wendell werner wes wesley weston whitney wilber wilbert
wilbur wilburn wiley wilford wilfred wilfredo will willard william williams willian willie willis willy
wilmer wilson wilton winford winfred winston wm woodrow wyatt xavier yong young zachariah zachary zachery
zack zackary zane

smith johnson williams brown jones miller davis garcia rodriguez wilson martinez anderson taylor thomas
hernandez moore martin jackson thompson white lopez lee gonzalez harris clark lewis robinson walker
perez hall young allen sanchez wright king scott green baker adams nelson hill ramirez campbell mitchell
roberts carter phillips evans turner torres parker collins edwards stewart flores morris nguyen murphy
rivera cook rogers morgan peterson cooper reed bailey bell gomez kelly howard ward cox diaz richardson
wood watson brooks bennett gray james reyes cruz hughes price myers long foster sanders ross morales
powell sullivan russell ortiz jenkins gutierrez perry butler barnes fisher henderson coleman simmons
patterson jordan reynolds hamilton graham kim gonzales alexander ramos wallace griffin west cole hayes
chavez gibson bryant ellis stevens murray ford marshall owens mcdonald harrison ruiz kennedy wells
alvarez woods mendoza castillo olson webb washington tucker freeman burns henry vasquez snyder simpson
crawford jimenez porter mason shaw gordon wagner hunter romero hicks dixon hunt palmer robertson black
holmes stone meyer boyd mills warren fox rose rice moreno schmidt patel ferguson nichols herrera medina
ryan fernandez weaver daniels stephens gardner payne kelley dunn pierce arnold tran spencer peters
hawkins grant hansen castro hoffman hart elliott cunningham knight bradley carroll hudson duncan
armstrong berry andrews johnston ray lane riley carpenter perkins aguilar silva richards willis matthews
chapman lawrence garza vargas watkins wheeler larson carlson harper george greene burke guzman morrison
munoz jacobs obrien lawson franklin lynch bishop carr salazar austin mendez gilbert jensen williamson
montgomery harvey oliver howell dean hanson weber garrett sims burton fuller soto mccoy welch chen
schultz walters reid fields walsh little fowler bowman davidson may day schneider newman brewer lucas
holland wong banks santos curtis pearson delgado valdez pena rios douglas sandoval barrett hopkins keller
guerrero stanley bates alvarado beck ortega wade estrada contreras barnett caldwell santiago lambert
powers chambers nunez craig leonard lowe rhodes byrd gregory shelton frazier becker maldonado fleming
vega sutton cohen jennings parks mcdaniel watts barker norris vaughn vazquez holt schwartz steele benson
neal dominguez horton terry wolfe hale lyons graves haynes miles park warner padilla bush thornton
mccarthy mann zimmerman erickson fletcher mckinney page dawson joseph marquez reeves klein espinoza
baldwin moran love robbins higgins ball cortez le griffith bowen sharp cummings ramsey hardy swanson
barber acosta luna chandler blair daniel cross simon dennis oconnor quinn gross navarro moss fitzgerald
doyle mclaughlin rojas rodgers stevenson singh yang figueroa harmon newton paul manning garner mcgee
reese francis burgess adkins goodman curry brady christensen potter walton goodwin mullins molina webster
fischer campos avila sherman todd chang blake malone wolf hodges juarez gill farmer hines gallagher duran
hubbard cannon miranda wang saunders tate mack hammond carrillo townsend wise ingram barton mejia ayala
schroeder hampton rowe parsons frank waters strickland osborne maxwell chan deleon norman harrington
casey patton logan bowers mueller glover floyd hartman buchanan cobb french kramer mccormick clarke tyler
gibbs moody conner sparks mcguire leon bauer norton pope flynn hogan robles salinas yates lindsey lloyd
marsh mcbride owen solis pham lang pratt lara brock ballard trujillo shaffer drake roman aguirre morton
stokes lamb pacheco patrick cochran shepherd cain burnett hess li cervantes olsen briggs ochoa cabrera
velasquez montoya roth meyers cardenas fuentes weiss hoover wilkins nicholson underwood short carson
morrow colon holloway summers bryan petersen mckenzie serrano wilcox carey clayton poole calderon gallegos
greer rivas guerra decker collier wall whitaker bass flowers davenport conley houston huff copeland hood
monroe massey roberson combs franco larsen pittman randall skinner wilkinson kirby cameron bridges anthony
richard kirk bruce singleton mathis bradford boone abbott charles allison sweeney atkinson horn jefferson
rosales york christian phelps farrell castaneda nash dickerson bond wyatt foley chase gates vincent mathews
hodge garrison trevino villarreal heath dalton valencia callahan hensley atkins huffman roy boyer shields
lin hancock grimes glenn cline delacruz camacho dillon parrish oneill melton booth kane berg harrell pitts
savage wiggins brennan salas marks russo sawyer baxter golden hutchinson liu walter mcdowell wiley rich
humphrey johns koch suarez hobbs beard gilmore ibarra keith macias khan andrade ware stephenson henson
wilkerson dyer mcclure blackwell mercado tanner eaton clay barron beasley oneal preston small wu zamora
macdonald vance snow mcclain stafford orozco barry english shannon kline jacobson woodard huang kemp
mosley prince merritt hurst villanueva roach nolan lam yoder mccullough lester santana valenzuela winters
barrera leach orr berger mckee strong conway stein whitehead bullock escobar knox meadows solomon velez
odonnell kerr stout blankenship browning kent lozano bartlett pruitt buck barr gaines durham gentry
mcintyre sloan melendez rocha herman sexton moon hendricks rangel stark lowery hardin hull sellers ellison
calhoun gillespie mora knapp mccall morse dorsey weeks nielsen livingston leblanc mclean bradshaw glass
middleton buckley schaefer frost howe house mcintosh ho pennington reilly hebert mcfarland hickman noble
spears conrad arias galvan velazquez huynh frederick randolph cantu fitzpatrick mahoney peck villa michael
donovan mcconnell walls boyle mayer zuniga giles pineda pace hurley mays mcmillan crosby ayers case
bentley shepard everett pugh david mcmahon dunlap bender hahn harding acevedo raymond blackburn duffy
landry dougherty bautista shah potts arroyo valentine meza gould vaughan fry rush avery herring dodson
clements sampson tapia bean lynn crane farley cisneros benton ashley mckay finley best blevins friedman
moses sosa blanchard huber frye krueger bernard rosario rubio mullen benjamin haley chung moyer choi
horne yu s s woodward ali nixon hayden rivers estes mccarty richmond stuart maynard brandt oconnell hanna
sanford sheppard church burch levy rasmussen coffey ponce faulkner donaldson schmitt novak costa montes
booker cordova waller arellano maddox mata bonilla stanton compton kaufman dudley mcpherson beltran
dickson mccann villegas proctor hester cantrell daugherty cherry bray davila rowland levine madden spence
good irwin werner krause petty whitney baird hooper pollard zavala jarvis holden haas hendrix mcgrath
bird lucero terrell riggs joyce mercer rollins galloway duke odom andersen downs hatfield benitez archer
huerta travis mcneil hinton zhang hays mayo fritz branch mooney ewing ritter esparza frey braun gay
riddle haney kaiser holder chaney mcknight gamble vang cooley carney cowan forbes ferrell davies barajas
shea osborn bright cuevas bolton murillo lutz duarte kidd key cooke

Jay Dee DeAnne Kenzie Marcyes Mark Hendrickson Peter Sauer John Rico Charles Zim Jean Dubois Rasczak
Jelal Dizzy Flores charlie Young CJ Cregg Mandy Hampton Sam Seaborn Donna Moss Toby Ziegler Josiah
Jed Bartlet Leo McGarry Josh Lyman Will Bailey Kate Harper Annabeth Schott Matt Santos Arnold Vinick
Homer Simpson Marge Simpson Bart Simpson Lisa Simpson Maggie Simpson Ned Flanders Maude Flanders
Rod Flanders Todd Flanders Itchy Scratchy Troy McClure Nelson Muntz Clancy Wiggum Ralph Wiggum Krusty
Willie Blossom Bubbles Buttercup Abigail Bartlet
''')

# via: http://www.lipsum.com/feed/html
_paragraphs = u'''
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Phasellus
pharetra urna sit amet magna. Donec posuere porta velit. Vestibulum sed libero.
Ut vestibulum sodales arcu. Proin vulputate, mi quis luctus ornare, elit ligula fringilla nisi,
eu tempor purus felis a enim. Phasellus in justo et nisi rhoncus porttitor. Donec ligula felis,
sagittis at, vestibulum eu, vehicula sed, nisl. Aenean convallis pharetra nisl. Mauris imperdiet
libero eu urna ultrices vulputate. Donec semper nunc et nibh. In hac habitasse platea dictumst.
Fusce et ipsum semper velit tempor pharetra. Donec pretium sollicitudin purus. Cras mi velit,
egestas id, ultrices vitae, viverra sit amet, justo.

Quisque cursus tristique nunc. Fusce varius, orci et pellentesque aliquet,
nibh ipsum sodales lorem, iaculis tincidunt massa metus ut erat. Fusce dictum,
dolor ut laoreet aliquam, massa urna placerat nibh, vitae tristique nisl neque posuere mi.
Aliquam at orci. Nulla sem. Nullam risus. Nullam pharetra dapibus mauris. Mauris mollis pretium arcu.
Vestibulum sem massa, tempor a, dictum id, rutrum eu, ligula. Class aptent taciti sociosqu ad
litora torquent per conubia nostra, per inceptos himenaeos. Curabitur ultrices dignissim nibh.
Aenean nisl.

Integer bibendum pharetra orci. Suspendisse commodo, lorem elementum egestas hendrerit,
metus elit rutrum sapien, quis aliquam nibh nisi at ligula. Nam lobortis commodo mauris.
Vivamus semper, leo vel accumsan mattis, nulla elit vestibulum augue, vitae pharetra dolor nibh
sit amet odio. Pellentesque scelerisque ipsum id elit. Nulla aliquet semper dolor. Praesent ut lorem.
Curabitur dictum, magna eu porttitor rutrum, ipsum justo porttitor erat, sit amet tristique est ante
ut elit. Mauris vel est. In cursus, velit quis pharetra adipiscing, purus quam sagittis mi,
eget molestie leo lectus ac lacus. Curabitur ante massa, aliquam ut, scelerisque a, condimentum at,
eros. Nunc vitae neque. Nam sagittis scelerisque magna. Class aptent taciti sociosqu ad litora
torquent per conubia nostra, per inceptos himenaeos. Donec cursus pede. Quisque a mauris nec
turpis convallis scelerisque. Donec quam lorem, mollis vestibulum, euismod in, hendrerit et, sapien.
Curabitur felis.

Morbi pretium lorem imperdiet dui. Maecenas quis ligula. Morbi tempor velit sit amet felis.
Donec at dui. Donec neque. Quisque quis mauris a libero ultrices iaculis. Integer congue feugiat justo.
Quisque imperdiet lectus eu orci. Class aptent taciti sociosqu ad litora torquent per conubia nostra,
per inceptos himenaeos. Vivamus id lectus. Phasellus odio nisi, auctor eu, hendrerit quis,
iaculis sit amet, felis. Sed blandit mollis nunc. Sed velit magna, tristique tristique, porttitor ut,
dictum a, arcu. In hac habitasse platea dictumst. Cras semper bibendum tortor. Cum sociis natoque
penatibus et magnis dis parturient montes, nascetur ridiculus mus. Suspendisse potenti.
In hac habitasse platea dictumst. Fusce mi sem, varius vitae, molestie ut, gravida venenatis, nibh.
Nam risus lectus, interdum at, condimentum eu, aliquet et, ipsum.

Mauris mi tortor, elementum ut, mattis eget, aliquam a, tellus.
Suspendisse porttitor orci. Donec rutrum diam non est. Duis ac nunc. Cras sollicitudin aliquet mi.
Cras in pede. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;
Nam vehicula est at metus. Suspendisse sapien. Nunc lobortis tortor sed purus hendrerit pellentesque.
Nunc laoreet. Morbi pharetra. Integer cursus molestie turpis. Nam cursus sodales sem.
Maecenas non lacus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames
ac turpis egestas. Nam vel nibh eu nulla blandit facilisis. Sed varius turpis ac neque.
Curabitur vel erat. Morbi sed purus id erat tincidunt ullamcorper.
'''

_words = re.split(r'\s+', _paragraphs)

