'''
a module to make it easy to get some test data

NOTE: all methods that return strings will return unicode utf-8 strings

for a utf-8 stress test, see: http://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
you can get all the unicode chars and their names: ftp://ftp.unicode.org/
    ftp://ftp.unicode.org/Public/6.3.0/ucd/UnicodeData-6.3.0d2.txt
'''
import re
import random
import string
import sys
import tempfile
import os
import codecs
import datetime
from random import randint # make it possible to do testdata.randint so 2 imports aren't needed
from collections import deque
import types

__version__ = '0.5.8'

def create_file_structure(path_str, tmpdir=u""):
    """
    create a whole file structure with a string, one file/directory per line

    NOTE -- the directories always have to end with /

    path_str -- string -- a multiline python string
    tmpdir -- string -- the root
    """
    path_lines = []
    if isinstance(path_str, types.StringTypes):
        path_lines = filter(None, path_str.split(os.linesep))
    else:
        path_lines = path_str

    dirs = set() # directories will always end with /
    files = set()
    depth_queue = deque()
    depth_queue.appendleft(0)
    path_prefix = deque()
    path_prefix.appendleft([])
    current_path = []

    for path in path_lines:
        # get the size of the whitespace:
        m = re.match("^\s*", path)
        current_depth = len(m.group(0))

        if current_depth > depth_queue[0]:
            depth_queue.appendleft(current_depth)
            path_prefix.appendleft(current_path)

        elif current_depth < depth_queue[0]:
            while current_depth < depth_queue[0]:
                depth_queue.popleft()
                path_prefix.popleft()

            if len(path_prefix) == 0:
                path_prefix.appendleft([])

            if len(depth_queue) == 0:
                depth_queue.appendleft(0)


        p = path.strip()
        is_dir = p.endswith("/") or p.endswith(os.sep)
        p = _normpath(p)

        #pout.b(p)
        #pout.v(current_depth, path_prefix, depth_queue)
        if p:
            full_path = filter(None, list(path_prefix[0]) + p.split(os.sep))
            if is_dir:
                dirs.add(os.sep.join(full_path))
            else:
                file_path = os.sep.join(full_path)
                dir_path = os.path.dirname(file_path)
                files.add(file_path)
                dirs.add(dir_path)

                full_path = filter(None, dir_path.split(os.sep))

            current_path = full_path

    if not tmpdir: tmpdir = tempfile.mkdtemp()

    ret_dirs = []
    for d in dirs:
        ret_dirs.append(create_dir(d, tmpdir=tmpdir))

    ret_files = []
    for f in files:
        ret_files.append(create_file(f, tmpdir=tmpdir))

    return tmpdir, ret_dirs, ret_files


def create_dir(path=u"", tmpdir=u""):
    '''
    create a directory path using a tempdir as the root

    so, if you pass in "/foo/bar" that will be combined with a tempdir, so you end 
    up with the final path: /tmp/python/dir/foo/bar

    path -- string -- the temp dir path
    tmpdir -- string -- the temp directory to use as the base

    return -- string -- the full directory path
    '''
    if path and path[0] == u'.':
        raise ValueError("you cannot start a path with ./ or ../")

    oldmask = os.umask(0)
    if not tmpdir: tmpdir = tempfile.mkdtemp()

    dirs = filter(None, _normpath(path).split(os.sep))
    d = os.path.join(tmpdir, *dirs)
    if not os.path.isdir(d):
        os.makedirs(d)

    os.umask(oldmask)
    return d

def create_file(path, contents=u"", tmpdir=u""):
    '''
    create a file and return the full path to that file

    path -- string -- the path to the file
    contents -- string -- the file contents
    tmpdir -- string -- the temp directory to use as the base

    return -- string -- the full file path
    '''
    if not tmpdir: tmpdir = tempfile.mkdtemp()

    path = _normpath(path)
    dir_path, filename = os.path.split(path)
    base_path = create_dir(dir_path, tmpdir)
    file_path = os.path.join(base_path, filename)

    oldmask = os.umask(0)
    f = codecs.open(file_path, encoding='utf-8', mode='w+')
    f.truncate(0)
    f.seek(0)
    f.write(contents)
    f.close()
    oldmask = os.umask(oldmask)

    return file_path


def create_files(file_dict, tmpdir=u""):
    """
    create a whole bunch of files all at once

    file_dict -- dict -- keys are the file_name, values are the file contents
    tmpdir -- string -- same as create_module() tmpdir
    """
    ret_files = []
    base_dir = create_dir(u"", tmpdir)

    for file_name, contents in file_dict.iteritems():
        ret_files.append(create_file(file_name, contents, base_dir))

    return ret_files


def create_modules(module_dict, tmpdir=u"", make_importable=True):
    """
    create a whole bunch of modules all at once

    module_dict -- dict -- keys are the module_name, values are the module contents
    tmpdir -- string -- same as create_module() tmpdir
    make_importable -- boolean -- same as create_module() tmpdir
    """
    ret_modules = []
    module_base_dir = create_dir(u"", tmpdir)

    for module_name, contents in module_dict.iteritems():
        ret_modules.append(create_module(module_name, contents, module_base_dir, make_importable))
        make_importable = False

    return ret_modules


def create_module(module_name, contents=u"", tmpdir=u"", make_importable=True):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported

    return -- string -- the module file path
    '''
    module_file = ''
    mod_bits = filter(None, module_name.split(u'.'))
    module_base_dir = create_dir(u"", tmpdir=tmpdir)
    base_modname = mod_bits.pop()

    base_dir = module_base_dir
    for modname in mod_bits:
        # check to see if there is a file that already exists
        mod_file = os.path.join(base_dir, u"{}.py".format(modname))

        # turn module.py into a package (module/__init__.py)
        base_dir = create_dir(modname, base_dir)
        if os.path.isfile(mod_file):
            os.rename(mod_file, os.path.join(base_dir, u"__init__.py"))
        else:
            # only add a blank package sentinel file if one already doesn't exist
            if not os.path.isfile(os.path.join(base_dir, u"__init__.py")):
                create_file(u"__init__.py", tmpdir=base_dir)

    mod_dir = os.path.join(base_dir, base_modname)
    if os.path.isdir(mod_dir):
        module_file = create_file(u"__init__.py", contents=contents, tmpdir=mod_dir)
    else:
        module_file = create_file(u"{}.py".format(base_modname), contents=contents, tmpdir=base_dir)

    # add the path to the top of the sys path so importing the new module will work
    if make_importable:
        sys.path.insert(0, module_base_dir) 

    return module_file


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

    if chars is None, this can generate up to a 4-byte utf-8 unicode string, which can
    break legacy utf-8 things
    
    str_size -- integer -- how long you want the string to be
    chars -- sequence -- the characters you want the string to use, if this is None, it
        will default to pretty much the entire unicode range of characters
    return -- unicode
    '''
    if str_size == 0:
        str_size = random.randint(3, 20)

    sg = None

    if chars is None:
        # chars can be any range in unicode (based off of table 3.7 of Unicode 6.2.0
        # pg 42 - http://www.unicode.org/versions/Unicode6.2.0/ch03.pdf
        # via: http://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
        byte_range = lambda first, last: range(first, last+1)
        first_values = byte_range(0x00, 0x7F) + byte_range(0xC2, 0xF4)
        trailing_values = byte_range(0x80, 0xBF)

        def random_utf8_seq():
            while True:
                first = random.choice(first_values)
                if first <= 0x7F: # U+0000...U+007F
                    return bytearray([first])
                elif (first >= 0xC2) and (first <= 0xDF): # U+0080...U+07FF
                    return bytearray([first, random.choice(trailing_values)])
                elif first == 0xE0: # U+0800...U+0FFF
                    return bytearray([first, random.choice(byte_range(0xA0, 0xBF)), random.choice(trailing_values)])
                elif (first >= 0xE1) and (first <= 0xEC): # U+1000...U+CFFF
                    return bytearray([first, random.choice(trailing_values), random.choice(trailing_values)])
                elif first == 0xED: # U+D000...U+D7FF
                    return bytearray([first, random.choice(byte_range(0x80, 0x9F)), random.choice(trailing_values)])
                elif (first >= 0xEE) and (first <= 0xEF): # U+E000...U+FFFF
                    return bytearray([first, random.choice(trailing_values), random.choice(trailing_values)])
                else:
                    if sys.maxunicode > 65535:
                        if first == 0xF0: # U+10000...U+3FFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(byte_range(0x90, 0xBF)),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )
                        elif (first >= 0xF1) and (first <= 0xF3): # U+40000...U+FFFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(trailing_values),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )
                        elif first == 0xF4: # U+100000...U+10FFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(byte_range(0x80, 0x8F)),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )

        sg = (random_utf8_seq().decode('utf-8') for c in xrange(str_size))

    else:
        # we have a defined set of chars
        sg = (random.choice(chars) for c in xrange(str_size))

    s = u''.join(sg)
    return s

def get_hex(str_size=0):
    '''
    generate a string of just hex characters

    str_size -- integer -- how long you want the string to be
    return -- unicode
    '''
    return get_str(str_size=str_size, chars=string.hexdigits.lower())

def get_ascii(str_size=0):
    '''
    generate a random string full of just ascii characters
    
    str_size -- integer -- how long you want the string to be
    return -- unicode
    '''
    chars=string.ascii_letters + string.digits
    return get_str(str_size=str_size, chars=chars)

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

def get_posint(max_size=2**31-1):
    """
    just return a positive 32-bit integer, this is basically a wrapper around
    random.randint where you don't have to specify a minimum (or a maximum if you
    don't want)
    """
    min_size = 1
    return random.randint(min_size, max_size)

def get_int(min_size=1, max_size=sys.maxsize):
    return get_unique_int(min_size, max_size)

def get_int32(min_size=1):
    """returns a unique 32-bit positive integer"""
    return get_unique_int(min_size, 2**31-1)

def get_int64(min_size=1):
    """returns up to a unique 64-bit positive integer"""
    return get_unique_int(min_size, 2**63-1)

def get_unique_int(min_size=1, max_size=sys.maxsize):
    '''
    get a random integer

    no different than random.randint except that it guarrantees no int will be
    the same, and also you don't have to set a range, it will default to all max
    int size

    return -- integer 
    '''
    i = 0;
    found = False
    max_count = max_size - min_size
    for x in xrange(max_count):
        i = random.randint(min_size, max_size)
        if i not in _previous_ints:
            found = True
            _previous_ints.add(i)
            break

    assert found, "no unique ints from {} to {} could be found".format(min_size, max_size)
    return i

def get_ascii_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_ascii_words)

def get_unicode_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_unicode_words)

def get_words(word_count=0, as_str=True, words=None):
    '''
    get some amount of random words

    word_count -- integer -- how many words you want, 0 means a random amount (at most 20)
    as_str -- boolean -- True to return as string, false to return as list of words
    words -- list -- a list of words to choose from, defaults to unicode + ascii words

    return -- unicode|list -- your requested words
    '''

    # since we specified we didn't care, randomly choose how many surnames there should be
    if word_count == 0:
        word_count = random.randint(1, 20)

    if not words:
        words = _words

    ret_words = random.sample(words, word_count)
    return ret_words if not as_str else u' '.join(ret_words)

def get_birthday(as_str=False):
    """
    return a random YYYY-MM-DD

    as_str -- boolean -- true to return the bday as a YYYY-MM-DD string
    return -- datetime.date|string
    """
    year = random.randint(1950, 1999)
    month = random.randint(1, 12)
    day = 1
    if month == 2:
        day = random.randint(1, 28)
    elif month in [9, 4, 6, 11]:
        day = random.randint(1, 30)
    else:
        day = random.randint(1, 31)

    bday = datetime.date(year, month, day)
    if as_str:
        bday = "{:%Y-%m-%d}".format(bday)

    return bday

def get_email(name=u''):
    '''return a random email address'''
    if not name: name = get_ascii_name()

    email_domains = [
        u"yahoo.com",
        u"hotmail.com",
        u"outlook.com",
        u"aol.com",
        u"gmail.com",
        u"msn.com",
        u"comcast.net",
        u"hotmail.co.uk",
        u"sbcglobal.net",
        u"yahoo.co.uk",
        u"yahoo.co.in",
        u"bellsouth.net",
        u"verizon.com",
        u"earthlink.net",
        u"cox.net",
        u"rediffmail.com",
        u"yahoo.ca",
        u"btinternet.com",
        u"charter.net",
        u"shaw.ca",
        u"ntlworld.com",
        u"gmx.com",
        u"gmx.net",
        u"mail.com",
        u"mailinator.com"
    ]

    return u'{}@{}'.format(name.lower(), random.choice(email_domains))

def get_name(name_count=2, as_str=True):
    '''
    get a random name

    link -- http://stackoverflow.com/questions/30485/what-is-a-reasonable-length-limit-on-person-name-fields

    name_count -- integer -- how many total name parts you want (eg, "Jay marcyes" = 2 name_count)
    as_str -- boolean -- True to return as string, false to return as list of names

    return -- unicode|list -- your requested name
    '''
    # since we specified we didn't care, randomly choose how many surnames there should be
    if name_count <= 0:
        name_count = random.randint(1, 5)

    # decide if we should hyphenate the last name
    names = []
    if name_count > 0:
        #names = random.sample(_names, name_count)
        for x in xrange(name_count):
            if random.randint(0, 100) < 20:
                names.append(get_unicode_name())
            else:
                names.append(get_ascii_name())

        if name_count > 1:
            if random.randint(0, 20) == 1:
                names[-1] = u'{}-{}'.format(names[-1], random.choice(_names))

    return names if not as_str else u' '.join(names)

def get_ascii_name():
    '''return one ascii safe name'''
    return random.choice(_names)

def get_unicode_name():
    '''return one none ascii safe name'''
    name = u''
    while True:
        # total hack to get around not all the names in _unicode_names being unicode
        try:
            name = random.choice(_unicode_names)
            name.decode('utf-8')
        except UnicodeEncodeError:
            break

    return name
    # return random.choice(_unicode_names)

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

# all the names to choose from in get_name() (english and russian)
_names = re.split(r'\s+', u"""
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

Abbie-Leigh Abbie-Louise Abbie-May Aimee-Grace Aimee-Jo Aimee-Lea Aimee-Lee Aimee-Leigh
Aimee-Louise Aimee-Rose Alesha-Mae Alexa-Rose Alice-Mae Alice-May Alicia-Mae Alicia-May Alisha-May
Alisha-Rose Alissa-Mae Alyssa-Mae Amber-Leigh Amber-Louise Amber-Mae Amber-Rose Amelia-Grace Amelia-Jane
Amelia-Jayne Amelia-Mae Amelia-Mai Amelia-Rose Amelie-Grace Amelie-Rose Amie-Leigh Amy-Grace Amy-Jane
Amy-Jayne Amy-Jo Amy-Lea Amy-Lee Amy-Leigh Amy-Lou Amy-Louise Amy-May Amy-Rose Ana-Maria Angel-Louise Angel-Mae
Angel-Mai Angel-Marie Angel-Rose Anna-Leigh Anna-Louise Anna-Mae Anna-Maria Anna-Marie Anna-May
Anna-Rose Anna-Sophia Anne-Marie Annie-Mae Annie-Mai Annie-May Annie-Rose Ann-Marie Anya-Rose April-Rose
Autumn-Rose Ava-Grace Ava-Jane Ava-Jo Ava-Leigh Ava-Lily Ava-Louise Ava-Mae Ava-Mai Ava-Marie Ava-May
Ava-Nicole Ava-Rose Ava-Sophia Bailey-Mae Bailey-Rae Bella-Rose Bethany-Ann Bethany-Rose Billie-Jean Billie-Jo
Billie-Mae Billie-Rose Bobbie-Jo Bobbie-Leigh Bobbi-Jo Bonnie-May Brodie-Leigh Brooke-Elise Brooke-Leigh
Brooke-Louise Cara-Louise Carol-Ann Carrie-Ann Carrie-Anne Casey-Jayne Casey-Leigh Casey-Mae Casey-Marie
Casey-May Charlie-Mae Charlie-May Charlotte-Rose Chloe-Ann Chloe-Anne Chloe-Jade Chloe-Leigh Chloe-Louise Chloe-Mae
Chloe-Mai Chloe-Marie Chloe-May Chloe-Rose Chloe-Sophia Codie-Leigh Connie-Mae Connie-Rose Courtney-Jade
Courtney-Leigh Courtney-Rose Daisy-Ann Daisy-Boo Daisy-Leigh Daisy-Lou Daisy-Mae Daisy-Mai Daisy-May
Daisy-Rose Darcey-Leigh Darcey-May Darcie-Mae Darcie-Rose Darci-Leigh Darci-Rose Darcy-Mae Darcy-May
Demi-Elise Demi-Jo Demi-Lea Demi-Lee Demi-Leigh Demi-Lou Demi-Louise Demi-Mai Demi-Marie Demi-May Demi-Rae
Demi-Rose Destiny-Mai Dollie-Mai Ebony-Grace Ebony-Mae Ebony-Mai Ebony-Rose Eden-Rose Edie-Mae Eliza-Rose
Ella-Grace Ella-Jade Ella-Jai Ella-Jane Ella-Jayne Ella-Louise Ella-Mae Ella-Mai Ella-Marie Ella-May Ella-Rae
Ella-Rose Elle-Louise Elle-Mae Elle-Mai Elle-May Ellie-Ann Ellie-Anne Ellie-Grace Ellie-Jane Ellie-Jay Ellie-Jayne
Ellie-Jo Ellie-Leigh Ellie-Louise Ellie-Mae Ellie-Mai Ellie-Marie Ellie-May Ellie-Rae Ellie-Rose Elli-Mae
Elli-Mai Elsie-Mae Elsie-May Elsie-Rose Emily-Ann Emily-Anne Emily-Grace Emily-Jane Emily-Jayne Emily-Louise
Emily-Mae Emily-Mai Emily-May Emily-Rose Emma-Jane Emma-Jayne Emma-Leigh Emma-Louise Emmie-Lou Erin-Mae
Eva-Mae Eva-Maria Eva-Marie Eva-May Eva-Rose Evelyn-Rose Evie-Anne Evie-Grace Evie-Jane Evie-Jayne Evie-Jean
Evie-Jo Evie-Leigh Evie-Louise Evie-Mae Evie-Mai Evie-Marie Evie-May Evie-Rose Faatimah-Zahra Faith-Marie Felicity-Rose
Frankie-Lee Frankie-Leigh Freya-Grace Freya-Leigh Freya-Louise Freya-Mae Freya-Mai Freya-May Georgia-Leigh
Georgia-Mae Georgia-Mai Georgia-May Georgia-Rose Georgie-May Grace-Lily Gracie-Ann Gracie-Jane Gracie-Jayne
Gracie-Lea Gracie-Lee Gracie-Leigh Gracie-Lou Gracie-Mae Gracie-Mai Gracie-May Gracie-Rose Hailie-Jade Halle-Mae
Halle-Mai Hallie-Mae Hannah-Louise Hannah-Mae Hannah-May Hollie-Ann Hollie-Grace Hollie-Louise Hollie-Mae
Hollie-Mai Hollie-May Hollie-Rose Holly-Ann Holly-Louise Holly-Mae Holly-Mai Holly-Marie Holly-May Holly-Rose
Honey-Mae India-Rose Indie-Rose Isabella-Grace Isabella-Mae Isabella-Rose Isabelle-Rose Isla-Mae
Isla-May Isla-Rose Isobel-Rose Izzy-Mai Jaimee-Lee Jaimee-Leigh Jaime-Leigh Jamie-Lea Jamie-Lee Jamie-Leigh
Jamie-Louise Jasmine-Rose Jaycee-Leigh Jayme-Leigh Jaymie-Leigh Jessica-Jane Jessica-Leigh Jessica-Lily
Jessica-Louise Jessica-Mae Jessica-Mai Jessica-May Jessica-Paige Jessica-Rose Jessica-Taylor Jessie-Mai
Jodie-Leigh Josie-May Julie-Ann Kacey-Lee Kacey-Leigh Kacey-Louise Kacey-May Kacie-Ann Kacie-Leigh Kacie-Mae
Kacie-May Kaci-Leigh Kaci-Louise Kaci-Mae Kaci-May Kadie-Leigh Kady-Leigh Kara-Louise Kasey-Leigh Kate-Lynn
Katie-Ann Katie-Jane Katie-Jayne Katie-Jo Katie-Lee Katie-Leigh Katie-Louise Katie-Mae Katie-Mai Katie-Marie
Katie-May Katie-Rose Katy-Leigh Kaycee-Leigh Kaycie-Leigh Kaydee-Leigh Kaydie-Leigh Kayla-Mae Kayla-Mai
Kayla-May Kayla-Rose Kay-Leigh Kayleigh-Ann Kayleigh-May Keira-Lee Keira-Leigh Keira-Louise Keira-Marie Kelly-Anne
Kelsie-Ann Kerry-Ann Kerry-Anne Kiara-Leigh Kiera-Leigh Kiera-Louise Kira-Leigh Kitty-Rose Kyla-Mae Kyla-May
Kyra-Lea Kyra-Leigh Kyra-Louise Lacey-Ann Lacey-Anne Lacey-Jade Lacey-Jane Lacey-Jay Lacey-Jo Lacey-Leigh
Lacey-Louise Lacey-Mae Lacey-Mai Lacey-Marie Lacey-May Lacey-Rose Lacie-Leigh Lacie-Mae Lacie-Mai Lacie-May
Laci-Mai Laila-Mai Laila-Marie Laila-Rose Layla-Faye Layla-Grace Layla-Louise Layla-Mae Layla-Mai Layla-May
Layla-Rae Layla-Rose Leah-Louise Leah-Mae Leah-Marie Leah-May Leah-Rose Lexi-Ann Lexi-Anne Lexie-Grace Lexie-Jay
Lexie-Jayne Lexie-Jo Lexie-Leigh Lexie-Lou Lexie-Mae Lexie-Mai Lexie-May Lexie-Rae Lexie-Rose Lexi-Grace Lexi-Jane
Lexi-Jayne Lexi-Jo Lexi-Lea Lexi-Leigh Lexi-Lou Lexi-Louise Lexi-Mae Lexi-Mai Lexi-Marie Lexi-May Lexi-Rose Libby-Jane
Libby-Louise Libby-Mae Libby-Mai Libby-May Libby-Rose Liberty-Grace Lila-Grace Lilah-Grace Lila-Rose Lili-Mae
Lili-Mai Lili-May Lillie-Ann Lillie-Anne Lillie-Mae Lillie-Mai Lillie-Marie Lillie-May Lillie-Rae Lillie-Rose Lilli-Mae
Lilli-Mai Lilli-Rose Lilly-Ann Lilly-Anna Lilly-Anne Lilly-Belle Lilly-Ella Lilly-Grace Lilly-Jade Lilly-Jane
Lilly-Jayne Lilly-Jean Lilly-Jo Lilly-Louise Lilly-Mae Lilly-Mai Lilly-Marie Lilly-May Lilly-Rae Lilly-Rose Lilly-Sue
Lily-Ann Lily-Anna Lily-Anne Lily-Belle Lily-Beth Lily-Ella Lily-Faye Lily-Grace Lily-Jade Lily-Jane Lily-Jay
Lily-Jayne Lily-Jo Lily-Louise Lily-Mae Lily-Mai Lily-Marie Lily-May Lily-Rae Lily-Rose Lily-Sue Lisa-Marie Lola-Grace
Lola-Jo Lola-Louise Lola-Mae Lola-Mai Lola-May Lola-Rose Lucie-Jo Lucie-Mae Lucy-Ann Lucy-Anne Lucy-Jane Lucy-Jo
Lucy-Louise Lucy-Mae Lucy-May Lucy-Rose Lydia-Mae Lyla-Grace Lyla-Rose Macey-Leigh Macie-Lea Macie-Leigh Macie-Rose Macy-Jo
Maddie-Rose Maddison-Grace Maddison-Rose Madison-Grace Madison-Leigh Maisie-Ann Maisie-Grace Maisie-Jane Maisie-Jayne
Maisie-Jo Maisie-Lee Maisie-Leigh Maisie-Lou Maisie-Mae Maisie-May Maisie-Rose Maisy-Jane Maisy-May Mary-Ann
Mary-Anne Mary-Ellen Mary-Jane Mary-Jayne Mary-Kate Mary-Rose Matilda-Rose Mckenzie-Leigh Megan-Grace Megan-Leigh
Megan-Rose Melody-Rose Mia-Ann Mia-Grace Mia-Jade Mia-Jayne Mia-Jo Mia-Leigh Mia-Lily Mia-Louise Mia-Nicole Mia-Rose
Miley-Grace Miley-Jo Miley-Mae Miley-Mai Miley-Rae Miley-Rose Milli-Ann Millie-Ann Millie-Anne Millie-Grace Millie-Jayne
Millie-Jo Millie-Mae Millie-Mai Millie-May Millie-Rose Milly-May Milly-Rose Mollie-Ann Mollie-Louise Mollie-Mae
Mollie-May Mollie-Rose Molly-Ann Molly-Anne Molly-Jo Molly-Mae Molly-Mai Molly-May Molly-Rose Morgan-Leigh
Mya-Louise Mya-Rose Nancy-May Nevaeh-Rose Noor-Fatima Olivia-Grace Olivia-Jane Olivia-Leigh Olivia-Mae
Olivia-Mai Olivia-may Olivia-Paige Olivia-Rose Paige-Marie Phoebe-Lee Phoebe-Louise Phoebe-Rose Poppy-Ann
Poppy-Anne Poppy-Grace Poppy-Jo Poppy-Mae Poppy-Mai Poppy-May Poppy-Rose Ronnie-May Rose-Marie Rosie-Ann
Rosie-Leigh Rosie-Mae Rosie-Mai Rosie-May Rubie-Leigh Rubie-Mae Rubie-Mai Ruby-Ann Ruby-Anne Ruby-Blu Ruby-Grace
Ruby-Jane Ruby-Jean Ruby-Jo Ruby-Lea Ruby-Lee Ruby-Leigh Ruby-Lou Ruby-Louise Ruby-Mae Ruby-Mai Ruby-Marie
Ruby-May Ruby-Rae Ruby-Rose Sadie-Rose Sammi-Jo Sammy-Jo Sarah-Jane Sarah-Jayne Sarah-Louise Scarlet-Rose
Scarlett-Louise Scarlett-Mae Scarlett-Marie Scarlett-Rose Seren-Louise Shannon-Louise Shayla-Louise Shayla-Rae
Sienna-Grace Sienna-Lee Sienna-Leigh Sienna-Mae Sienna-Marie Sienna-May Sienna-Rose Skye-Louise Skye-Marie Skyla-Mae
Skyla-Mai Sky-Louise Sophia-Rose Sophie-Ann Sophie-Anne Sophie-Ella Sophie-Grace Sophie-Jane Sophie-Leigh
Sophie-Louise Sophie-Mae Sophie-Mai Sophie-Marie Sophie-May Sophie-Rose Stevie-Leigh Summer-Jade Summer-Jayne Summer-Lea
Summer-Leigh Summer-Lily Summer-Louise Summer-Mae Summer-Marie Summer-May Summer-Rose Sydney-Rose Tallulah-Mae
Taylor-Ann Taylor-Grace Taylor-Jane Taylor-Jay Taylor-Leigh Taylor-Louise Taylor-Mae Taylor-May Taylor-Rose
Tegan-Louise Tia-Leigh Tia-Louise Tia-Mae Tia-Mai Tia-Marie Tia-May Tia-Rae Tia-Rose Tiana-Leigh Tiana-Marie
Tianna-Marie Tiffany-Marie Tiger-Lilly Tiger-Lily Tillie-Mae Tillie-Mai Tilly-Mae Tilly-Mai Tilly-Marie Tilly-May
Tilly-Rose Toni-Ann Toni-Leigh Toni-Marie Tori-Lee Tori-Leigh Umme-Haani Violet-Rose Willow-Rose 

Aaron-James Abdul-Aziz Abdul-Hadi Abdul-Malik Abdul-Raheem Abdul-Rahim Abdul-Rahman Abdul-Rehman Abdul-Sami
Abdur-Raheem Abdur-Rahim Abdus-Samad Abu-Bakar Abu-Bakr Abu-Sufyan Aiden-James Aiden-Lee A-Jay Al-Amin
Alexander-James Alfie-Jack Alfie-Jai Alfie-James Alfie-Jay Alfie-Joe Alfie-John Alfie-Lee Alfie-Ray Andrew-James
Archie-Jay Archie-Lee Ashton-Lee Aston-Lee Bailey-James Bailey-Rae Billy-Jay Billy-Joe Billy-Lee Billy-Ray
Bobby-Jack Bobby-James Bobby-Jay Bobby-Joe Bobby-Lee Braiden-Lee Brandon-Lee Brogan-Lee Callum-James Cameron-James
Cameron-Jay Charlie-Dean Charlie-George Charlie-James Charlie-Jay Charlie-Joe Charlie-Ray C-Jay Cody-James
Cody-Jay Cody-Lee Conner-Lee Connor-James Connor-Jay Connor-Lee Corey-James Corey-Lee Daniel-James Daniel-Junior
Danny-Lee David-James Dylan-James Ethan-James Ethan-Lee Finley-James Frankie-Lee Freddie-Jay Freddie-Lee Harley-James
Harley-Jay Harley-Joe Harley-John Harley-Ray Harrison-Lee Harry-George Harry-James Harry-Lee Harvey-James Harvey-Jay
Harvey-Lee Harvey-Leigh Hayden-Lee Henry-James Jacob-James Jacob-Lee Jaiden-Lee James-Dean Jamie-Lee Jason-James
Jay-D Jaydan-Lee Jayden-James Jayden-Jay Jayden-John Jayden-Lee Jayden-Leigh Jay-Jay Jay-Junior Jay-Lee Jean-Paul
Jean-Pierre Jesse-James J-Jay Joe-Lewis Johnny-Lee John-Joseph John-Paul Jon-Paul Jordan-Lee Joseph-James Joshua-James
Joshua-Jay Junior-Jay Justin-Lee Kaiden-Lee Kal-El Kayden-Lee Keegan-Lee Kenzie-James Kenzie-Jay Kenzie-Lee
Kieran-Lee K-Jay Layton-James Layton-Lee Lee-Jay Leighton-James Leo-James Leon-Junior Levi-James Levi-Jay
Lewis-James Lewis-Lee Liam-James L-Jay Logan-James Logan-Jay Logan-Lee Louie-Jay Lucas-Jack Lucas-James
Lucas-Jay Mackenzie-Lee Marley-Lee Marley-Rae Mason-James Mason-Jay Mason-Lee Mckenzie-Jay Mckenzie-Lee
Michael-John Michael-Lee Mohamed-Amin Mohammed-Ibrahim Mohammed-Mustafa Muhammah-Ali Muhammad-Ibrahim Muhammad-Yusef
Nathan-Lee Oliver-James Owen-James Peter-Junior Ricky-Junior Riley-James Riley-Jay Riley-Joe Ronnie-Lee Russell-James
Ryan-James Ryan-Lee Saif-Ullah Sean-Paul Sonny-Lee Taylor-Jake Taylor-James Taylor-Jay Taylor-Lee Tee-Jay Thomas-James
Thomas-Jay Thomas-Lee T-Jay Tommy-Lee Tyler-Jack Tyler-Jake Tyler-James Tyler-Jay Tyler-Joe Tyler-Lee

Toa'ale, Hau'oli O'Brien, D'Angelo God'iss, Domi'nique De'wayne La'tanya D'Juan Rah'Nee A'merika Shau'Nay Mich'ele
N'cole A'Brianna Ma'Kayla Sha'tyana Zy'shonne November'Lashae Ja'Kingston and Ke'Shawn D'nasia
X'Zavier An'Gelina Cha'Nce O'Livia Dan'Yelle Jer'Miah Ky'Lee Rach'El Cie'Rrea Sh'nia J'siah
Cam'Ron Chanze'es Day'quandray D'Jon D'Monie Don'ta'ja Fiaavd'e I'Lanny Ja'sheem Day'twain Chris La'tko
L'Cole O'Jai O'Merion Q'ndell R'Son Sei'Jearr Ta'Quwereus Ted'Quarius Xa'Viance za'Veann Z'Jayden 
A'jA Anah'reya A'Majena Be'aJa Cier'rrea D'aSiyahna R'yaire D'Kota E'ryn I'Zeyonna Ja'genevia JaKeil'a Ta-Shay
Ja'mya Jane't Kei'Lee Ken'yel K'le Mi'Angel N'finique Sanai' Sh'nia Syn'Cere Syri'yah Ti-Leigh'yah
Zae'kee Zy'Erica Zy'rreah 
""".strip())

_unicode_names = re.split(r'\s+', u"""
\u0410\u0431\u0440\u0430\u043c Abram \u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440 Alexander
\u0410\u043b\u0435\u043a\u0441\u0435\u0439 Alexei \u0410\u043b\u044c\u0431\u0435\u0440\u0442 Albert
\u0410\u043d\u0430\u0442\u043e\u043b\u0438\u0439 Anatoly \u0410\u043d\u0434\u0440\u0435\u0439 Andrei
\u0410\u043d\u0442\u043e\u043d Anton \u0410\u0440\u043a\u0430\u0434\u0438\u0439 Arkady \u0410\u0440\u0441\u0435\u043d\u0438\u0439
Arseny \u0410\u0440\u0442\u0451\u043c Artyom \u0410\u0440\u0442\u0443\u0440 Artur \u0410\u0444\u0430\u043d\u0430\u0441\u0438\u0439
Afanasy \u0411\u043e\u0433\u0434\u0430\u043d Bogdan \u0411\u043e\u0440\u0438\u0441 Boris \u0412\u0430\u0434\u0438\u043c
Vadim \u0412\u0430\u043b\u0435\u043d\u0442\u0438\u043d Valentin \u0412\u0430\u043b\u0435\u0440\u0438\u0439 Valery
\u0412\u0430\u0441\u0438\u043b\u0438\u0439 Vasily \u0412\u0435\u043d\u0438\u0430\u043c\u0438\u043d Veniamin
\u0412\u0438\u043a\u0442\u043e\u0440 Viktor \u0412\u0438\u0442\u0430\u043b\u0438\u0439 Vitaly \u0412\u043b\u0430\u0434 Vlad
\u0412\u043b\u0430\u0434\u0438\u043c\u0438\u0440 Vladimir \u0412\u043b\u0430\u0434\u0438\u0441\u043b\u0430\u0432 Vladislav
\u0412\u0441\u0435\u0432\u043e\u043b\u043e\u0434 Vsevolod \u0412\u044f\u0447\u0435\u0441\u043b\u0430\u0432 Vyacheslav
\u0413\u0430\u0432\u0440\u0438\u0438\u043b Gavriil \u0413\u0430\u0440\u0440\u0438 Garry
\u0413\u0435\u043d\u043d\u0430\u0434\u0438\u0439 Gennady \u0413\u0435\u043e\u0440\u0433\u0438\u0439 Georgy
\u0413\u0435\u0440\u0430\u0441\u0438\u043c Gerasim \u0413\u0435\u0440\u043c\u0430\u043d German \u0413\u043b\u0435\u0431
Gleb \u0413\u0440\u0438\u0433\u043e\u0440\u0438\u0439 Grigory \u0414\u0430\u0432\u0438\u0434 David
\u0414\u0430\u043d\u0438\u0438\u043b Daniil \u0414\u0435\u043d\u0438\u0441 Denis \u0414\u043c\u0438\u0442\u0440\u0438\u0439
Dmitry \u0415\u0432\u0433\u0435\u043d\u0438\u0439 Evgeny \u0415\u0433\u043e\u0440 Yegor \u0415\u0444\u0438\u043c Yefim
\u0417\u0430\u0445\u0430\u0440 Zakhar \u0418\u0432\u0430\u043d Ivan \u0418\u0433\u043d\u0430\u0442
\u0418\u0433\u043d\u0430\u0442\u0438\u0439  eegNAHteey  Ignaty \u0418\u0433\u043e\u0440\u044c Igor
\u0418\u043b\u043b\u0430\u0440\u0438\u043e\u043d Illarion \u0418\u043b\u044c\u044f Ilia
\u0418\u043c\u043c\u0430\u043d\u0443\u0438\u043b Immanuil \u0418\u043e\u0441\u0438\u0444 Iosif
\u041a\u0438\u0440\u0438\u043b\u043b Kirill \u041a\u043e\u043d\u0441\u0442\u0430\u043d\u0442\u0438\u043d Konstantin
\u041b\u0435\u0432 Lev/Leo \u041b\u0435\u043e\u043d\u0438\u0434 Leonid \u041c\u0430\u043a\u0430\u0440 Makar
\u041c\u0430\u043a\u0441\u0438\u043c Maxim \u041c\u0430\u0440\u0430\u0442 Marat \u041c\u0430\u0440\u043a Mark
\u041c\u0430\u0442\u0432\u0435\u0439 Matvei \u041c\u0438\u0445\u0430\u0438\u043b Mikhail
\u041d\u0435\u0441\u0442\u043e\u0440 Nestor \u041d\u0438\u043a\u0438\u0442\u0430 Nikita
\u041d\u0438\u043a\u043e\u043b\u0430\u0439 Nikolay \u041e\u043b\u0435\u0433 Oleg \u041f\u0430\u0432\u0435\u043b
Pavel \u041f\u0451\u0442\u0440 Pyotr/Peter \u0420\u043e\u0431\u0435\u0440\u0442 Robert
\u0420\u043e\u0434\u0438\u043e\u043d Rodion \u0420\u043e\u043c\u0430\u043d Roman
\u0420\u043e\u0441\u0442\u0438\u0441\u043b\u0430\u0432 Rostislav \u0420\u0443\u0441\u043b\u0430\u043d Ruslan
\u0421\u0435\u043c\u0451\u043d Semyon \u0421\u0435\u0440\u0433\u0435\u0439 Sergei \u0421\u043f\u0430\u0440\u0442\u0430\u043a
Spartak \u0421\u0442\u0430\u043d\u0438\u0441\u043b\u0430\u0432 Stanislav \u0421\u0442\u0435\u043f\u0430\u043d
Stepan \u0422\u0430\u0440\u0430\u0441 Taras \u0422\u0438\u043c\u043e\u0444\u0435\u0439 Timofei
\u0422\u0438\u043c\u0443\u0440 Timur \u0422\u0440\u043e\u0444\u0438\u043c Trofim \u042d\u0434\u0443\u0430\u0440\u0434
Eduard \u042d\u0440\u0438\u043a Erik \u042e\u043b\u0438\u0430\u043d Yulian \u042e\u0440\u0438\u0439 Yury
\u042f\u043a\u043e\u0432 Yakov \u042f\u0440\u043e\u0441\u043b\u0430\u0432 Yaroslav 
\u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440\u0430 Alexandra \u0410\u043b\u0438\u043d\u0430
Alina \u0410\u043b\u0438\u0441\u0430 Alisa \u0410\u043b\u043b\u0430 Alla \u0410\u043b\u0451\u043d\u0430
Alyona \u0410\u043b\u044c\u0431\u0438\u043d\u0430 Albina \u0410\u043d\u0430\u0441\u0442\u0430\u0441\u0438\u044f
Anastasiya \u0410\u043d\u043d\u0430 Anna \u0410\u043d\u0442\u043e\u043d\u0438\u043d\u0430 Antonina
\u0410\u043d\u0436\u0435\u043b\u0438\u043a\u0430 Anzhelika \u0410\u043d\u0444\u0438\u0441\u0430 Anfisa
\u0412\u0435\u0440\u0430 Vera \u0412\u0430\u043b\u0435\u0440\u0438\u044f Valeriya \u0412\u0430\u0440\u0432\u0430\u0440\u0430
Varvara \u0412\u0430\u0441\u0438\u043b\u0438\u0441\u0430 Vasilisa \u0412\u043b\u0430\u0434\u043b\u0435\u043d\u0430
Vladlena \u0412\u0435\u0440\u043e\u043d\u0438\u043a\u0430 Veronika \u0412\u0430\u043b\u0435\u043d\u0442\u0438\u043d\u0430
Valentina \u0412\u0438\u043a\u0442\u043e\u0440\u0438\u044f Viktoriya \u0413\u0430\u043b\u0438\u043d\u0430
Galina \u0414\u0430\u0440\u044c\u044f Darya \u0414\u0438\u043d\u0430 Dina \u0414\u0438\u0430\u043d\u0430
Diana \u0414\u043e\u043c\u0438\u043d\u0438\u043a\u0430 Dominika \u0415\u043a\u0430\u0442\u0435\u0440\u0438\u043d\u0430
Ekateirna \u0415\u043b\u0435\u043d\u0430 Elena \u0415\u043b\u0438\u0437\u0430\u0432\u0435\u0442\u0430 Elizaveta
\u0415\u0432\u0433\u0435\u043d\u0438\u044f Evgeniya \u0415\u0432\u0430 Eva \u0416\u0430\u043d\u043d\u0430 Zhanna
\u0417\u0438\u043d\u0430\u0438\u0434\u0430 Zinaida \u0417\u043e\u044f Zoya \u0417\u043b\u0430\u0442\u0430 Zlata
\u0418\u043d\u0433\u0430 Inga \u0418\u043d\u043d\u0430 Inna \u0418\u0440\u0438\u043d\u0430 Irina
\u0418\u043d\u0435\u0441\u0441\u0430 Inessa \u0418\u0437\u0430\u0431\u0435\u043b\u043b\u0430 Izabella
\u0418\u0437\u043e\u043b\u044c\u0434\u0430 Izolda \u0418\u0441\u043a\u0440\u0430 Iskra \u041a\u043b\u0430\u0440\u0430
Klara \u041a\u043b\u0430\u0432\u0434\u0438\u044f Klavdiya \u041a\u0441\u0435\u043d\u0438\u044f Kseniya
\u041a\u0430\u043f\u0438\u0442\u043e\u043b\u0438\u043d\u0430 Kapitolina \u041a\u043b\u0435\u043c\u0435\u043d\u0442\u0438\u043d\u0430
Klementina \u041a\u0440\u0438\u0441\u0442\u0438\u043d\u0430 Kristina \u041b\u0430\u0434\u0430 Lada
\u041b\u0430\u0440\u0438\u0441\u0430 Larisa \u041b\u0438\u0434\u0438\u044f Lidiya \u041b\u044e\u0431\u043e\u0432\u044c
Lubov \u041b\u0438\u043b\u0438\u044f Liliya \u041b\u044e\u0434\u043c\u0438\u043b\u0430 Ludmila
\u041b\u044e\u0441\u044f Lucya \u041c\u0430\u0440\u0433\u0430\u0440\u0438\u0442\u0430 Margarita
\u041c\u0430\u0439\u044f Maya \u041c\u0430\u043b\u044c\u0432\u0438\u043d\u0430 Malvina \u041c\u0430\u0440\u0442\u0430
Marta \u041c\u0430\u0440\u0438\u043d\u0430 Marina \u041c\u0430\u0440\u0438\u044f Mariya \u041d\u0430\u0434\u0435\u0436\u0434\u0430
Nadezhda \u041d\u0430\u0442\u0430\u043b\u044c\u044f Natalya \u041d\u0435\u043b\u043b\u0438 Nelly \u041d\u0438\u043d\u0430
Nina \u041d\u0438\u043a\u0430 Nika \u041d\u043e\u043d\u043d\u0430 Nonna \u041e\u043a\u0441\u0430\u043d\u0430 Oksana
\u041e\u043b\u044c\u0433\u0430 Olga \u041e\u043b\u0435\u0441\u044f Olesya \u041f\u043e\u043b\u0438\u043d\u0430
Polina \u0420\u0430\u0438\u0441\u0430 Raisa \u0420\u0430\u0434\u0430 Rada \u0420\u043e\u0437\u0430\u043b\u0438\u043d\u0430
Rozalina \u0420\u0435\u0433\u0438\u043d\u0430 Regina \u0420\u0435\u043d\u0430\u0442\u0430 Renata
\u0421\u0432\u0435\u0442\u043b\u0430\u043d\u0430 Svetlana \u0421\u043e\u0444\u044c\u044f \u0421\u043e\u0444\u0438\u044f
Sofia \u0422\u0430\u0438\u0441\u0438\u044f Taisia \u0422\u0430\u043c\u0430\u0440\u0430 Tamara
\u0422\u0430\u0442\u044c\u044f\u043d\u0430 Tatyana \u0423\u043b\u044c\u044f\u043d\u0430 Ulyana
\u0424\u0430\u0438\u043d\u0430 Faina \u0424\u0435\u0434\u043e\u0441\u044c\u044f Fedosia
\u0424\u043b\u043e\u0440\u0435\u043d\u0442\u0438\u043d\u0430 Florentina \u042d\u043b\u044c\u0432\u0438\u0440\u0430
Elvira \u042d\u043c\u0438\u043b\u0438\u044f Emilia \u042d\u043c\u043c\u0430 Emma \u042e\u043b\u0438\u044f
Yuliya \u042f\u0440\u043e\u0441\u043b\u0430\u0432\u0430 Yaroslava \u042f\u043d\u0430 Yana

Rene\u2019e A\u2019Laysyn, D\u2019Kota \u2019Ese Cam\u2019Ron Da\u2019neyelle No\u2019elle ZI\u2019eyekel Miche\u2019le
""".strip())

# via: http://www.lipsum.com/feed/html
# russian is from: http://masterrussian.com/vocabulary/most_common_words.htm
# japanese (4bytes) are from: http://www.i18nguy.com/unicode/supplementary-test.html
_ascii_paragraphs = u'''
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

_unicode_paragraphs = u'''
\u0437\u043d\u0430\u0442\u044c \u043c\u043e\u0439 \u0434\u043e \u0438\u043b\u0438 \u0435\u0441\u043b\u0438
\u0432\u0440\u0435\u043c\u044f \u0440\u0443\u043a\u0430 \u043d\u0435\u0442 \u0441\u0430\u043c\u044b\u0439
\u043d\u0438 \u0441\u0442\u0430\u0442\u044c \u0431\u043e\u043b\u044c\u0448\u043e\u0439 \u0434\u0430\u0436\u0435
\u0434\u0440\u0443\u0433\u043e\u0439 \u043d\u0430\u0448 \u0441\u0432\u043e\u0439 \u043d\u0443 \u043f\u043e\u0434
\u0433\u0434\u0435 \u0434\u0435\u043b\u043e \u0435\u0441\u0442\u044c \u0441\u0430\u043c \u0440\u0430\u0437
\u0447\u0442\u043e\u0431\u044b \u0434\u0432\u0430 \u0442\u0430\u043c \u0447\u0435\u043c \u0433\u043b\u0430\u0437
\u0436\u0438\u0437\u043d\u044c \u043f\u0435\u0440\u0432\u044b\u0439 \u0434\u0435\u043d\u044c \u0442\u0443\u0442
\u0432\u043e \u043d\u0438\u0447\u0442\u043e \u043f\u043e\u0442\u043e\u043c \u043e\u0447\u0435\u043d\u044c
\u0441\u043e \u0445\u043e\u0442\u0435\u0442\u044c \u043b\u0438 \u043f\u0440\u0438 \u0433\u043e\u043b\u043e\u0432\u0430
\u043d\u0430\u0434\u043e \u0431\u0435\u0437 \u0432\u0438\u0434\u0435\u0442\u044c \u0438\u0434\u0442\u0438
\u0442\u0435\u043f\u0435\u0440\u044c \u0442\u043e\u0436\u0435 \u0441\u0442\u043e\u044f\u0442\u044c
\u0434\u0440\u0443\u0433 \u0434\u043e\u043c \u0441\u0435\u0439\u0447\u0430\u0441 \u043c\u043e\u0436\u043d\u043e
\u043f\u043e\u0441\u043b\u0435 \u0441\u043b\u043e\u0432\u043e \u0437\u0434\u0435\u0441\u044c
\u0434\u0443\u043c\u0430\u0442\u044c \u043c\u0435\u0441\u0442\u043e \u0441\u043f\u0440\u043e\u0441\u0438\u0442\u044c
\u0447\u0435\u0440\u0435\u0437 \u043b\u0438\u0446\u043e \u0447\u0442\u043e \u0442\u043e\u0433\u0434\u0430
\u0432\u0435\u0434\u044c \u0445\u043e\u0440\u043e\u0448\u0438\u0439 \u043a\u0430\u0436\u0434\u044b\u0439
\u043d\u043e\u0432\u044b\u0439 \u0436\u0438\u0442\u044c \u0434\u043e\u043b\u0436\u043d\u044b\u0439
\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043f\u043e\u0447\u0435\u043c\u0443
\u043f\u043e\u0442\u043e\u043c\u0443 \u0441\u0442\u043e\u0440\u043e\u043d\u0430 \u043f\u0440\u043e\u0441\u0442\u043e
\u043d\u043e\u0433\u0430 \u0441\u0438\u0434\u0435\u0442\u044c \u043f\u043e\u043d\u044f\u0442\u044c
\u0438\u043c\u0435\u0442\u044c \u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0439 \u0434\u0435\u043b\u0430\u0442\u044c
\u0432\u0434\u0440\u0443\u0433 \u043d\u0430\u0434 \u0432\u0437\u044f\u0442\u044c \u043d\u0438\u043a\u0442\u043e
\u0441\u0434\u0435\u043b\u0430\u0442\u044c \u0434\u0432\u0435\u0440\u044c \u043f\u0435\u0440\u0435\u0434
\u043d\u0443\u0436\u043d\u044b\u0439 \u043f\u043e\u043d\u0438\u043c\u0430\u0442\u044c
\u043a\u0430\u0437\u0430\u0442\u044c\u0441\u044f \u0440\u0430\u0431\u043e\u0442\u0430 \u0442\u0440\u0438
\u0432\u0430\u0448 \u0443\u0436 \u0437\u0435\u043c\u043b\u044f \u043a\u043e\u043d\u0435\u0446
\u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0447\u0430\u0441 \u0433\u043e\u043b\u043e\u0441
\u0433\u043e\u0440\u043e\u0434 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u043f\u043e\u043a\u0430
\u0445\u043e\u0440\u043e\u0448\u043e \u0434\u0430\u0432\u0430\u0442\u044c \u0432\u043e\u0434\u0430
\u0431\u043e\u043b\u0435\u0435 \u0445\u043e\u0442\u044f \u0432\u0441\u0435\u0433\u0434\u0430
\u0432\u0442\u043e\u0440\u043e\u0439 \u043a\u0443\u0434\u0430 \u043f\u043e\u0439\u0442\u0438
\u0441\u0442\u043e\u043b \u0440\u0435\u0431\u0451\u043d\u043e\u043a \u0443\u0432\u0438\u0434\u0435\u0442\u044c
\u0441\u0438\u043b\u0430 \u043e\u0442\u0435\u0446 \u0436\u0435\u043d\u0449\u0438\u043d\u0430
\u043c\u0430\u0448\u0438\u043d\u0430 \u0441\u043b\u0443\u0447\u0430\u0439 \u043d\u043e\u0447\u044c
\u0441\u0440\u0430\u0437\u0443 \u043c\u0438\u0440 \u0441\u043e\u0432\u0441\u0435\u043c
\u043e\u0441\u0442\u0430\u0442\u044c\u0441\u044f \u043e\u0431 \u0432\u0438\u0434 \u0432\u044b\u0439\u0442\u0438
\u0434\u0430\u0442\u044c \u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c \u043b\u044e\u0431\u0438\u0442\u044c
\u0441\u0442\u0430\u0440\u044b\u0439 \u043f\u043e\u0447\u0442\u0438 \u0440\u044f\u0434
\u043e\u043a\u0430\u0437\u0430\u0442\u044c\u0441\u044f \u043d\u0430\u0447\u0430\u043b\u043e
\u0442\u0432\u043e\u0439 \u0432\u043e\u043f\u0440\u043e\u0441 \u043c\u043d\u043e\u0433\u043e
\u0432\u043e\u0439\u043d\u0430 \u0441\u043d\u043e\u0432\u0430 \u043e\u0442\u0432\u0435\u0442\u0438\u0442\u044c
\u043c\u0435\u0436\u0434\u0443 \u043f\u043e\u0434\u0443\u043c\u0430\u0442\u044c \u043e\u043f\u044f\u0442\u044c
\u0431\u0435\u043b\u044b\u0439 \u0434\u0435\u043d\u044c\u0433\u0438 \u0437\u043d\u0430\u0447\u0438\u0442\u044c
\u043f\u0440\u043e \u043b\u0438\u0448\u044c \u043c\u0438\u043d\u0443\u0442\u0430 \u0436\u0435\u043d\u0430
'''

# only add 4-byte unicode if 4-byte unicode is supported
if sys.maxunicode > 65535:
    _unicode_paragraphs += u'''
\U0002070e \U00020731 \U00020779 \U00020c53 \U00020c78 \U00020c96 \U00020ccf \U00020cd5 \U00020d15 \U00020d7c
\U00020d7f \U00020e0e \U00020e0f \U00020e77 \U00020e9d \U00020ea2 \U00020ed7 \U00020ef9 \U00020efa \U00020f2d
\U00020f2e \U00020f4c \U00020fb4 \U00020fbc \U00020fea \U0002105c \U0002106f \U00021075 \U00021076 \U0002107b
\U000210c1 \U000210c9 \U000211d9 \U000220c7 \U000227b5 \U00022ad5 \U00022b43 \U00022bca \U00022c51 \U00022c55
\U00022cc2 \U00022d08 \U00022d4c \U00022d67 \U00022eb3 \U00023cb7 \U000244d3 \U00024db8 \U00024dea \U0002512b
\U00026258 \U000267cc \U000269f2 \U000269fa \U00027a3e \U0002815d \U00028207 \U000282e2 \U00028cca \U00028ccd
\U00028cd2 \U00029d98
'''

_ascii_words = re.split(ur'\s+', _ascii_paragraphs.strip())
_unicode_words = re.split(ur'\s+', _unicode_paragraphs.strip())
_words = _ascii_words + _unicode_words

def _normpath(path):
    '''
    normalize a path, accounting for things like windows dir seps

    for some reason, os.path.split() wouldn't work with the windows slash (\)
    '''
    if not path: return u''

    path = os.path.normpath(path)
    #dirs = filter(None, re.split(ur'[\\/]+', path))
    path = re.sub(r"[\\/]+", os.sep, path)
    return path
    #return os.sep.join(dirs)

