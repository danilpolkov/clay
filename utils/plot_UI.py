from PIL import Image, ImageDraw
import tensorflow as tf
import numpy as np
from collections import Counter, defaultdict
import matplotlib.patches as mpatches
import random
import matplotlib.pyplot as plt
import json


SCREEN_SIZE = (1440, 2560) # Do NOT change
ELEMENT_COLOR = {'EditText': 'orange',
                 #'edit': 'orange',
                 'CheckedTextView': 'lime',
                 'Text': 'blue',
                 'text': 'blue',
                 'TextView': 'blue',
                 'RadioButton': 'lime',
                 'Button': 'green',
                 #'button': 'green',
                 'Image': 'red',
                 'image': 'red',
                 'icon': 'red',
                 'CheckBox': 'pink',
                 'checkbox': 'pink',
                 'Checkbox': 'pink',
                 'checkBox': 'pink',
                 'WebView': 'purple',
                 'AdView': 'brown',
                 'Banner': 'brown',
                 'NumberPicker': 'gray',
                 'SpeedometerGauge': 'red',
                 'Gauge': 'red',
                 'ArcProgress': 'red',
                 'SimpleDraweeView': 'red',
                 'MonthView': 'yellow',
                 'AccessibleDateAnimator': 'yellow',
                 'MapView': 'skyblue',
                 'VideoView': 'navy',
                 'Chart': 'red',
                 'SeekBar': 'gold',
                 'PictureView': 'red',
                 'Picture': 'red',
                 'ActionMenuItemView': 'green',
                 'ImageSurfaceView': 'red',
                 'ImageView': 'red',
                 'SurfaceView': 'red',
                 'Graph': 'red',
                 'RadialPicker': 'ivory',
                 'time_picker': 'ivory',
                 'TimePicker': 'ivory',
                 'ProgressBar': 'magenta',
                 }

ELEMENT_EXCEPT = [#'feeditem',
                  #'edit_profile',
                  #'credit',
                  'background_holder',
                  'background_image',
                  ]

FULL_NAME_COLOR = {'google.maps.api.android': 'skyblue', # Google Maps API
                   'google.android.gms.ads': 'brown', # Google Ads
                   'mopub.mobileads': 'brown', # Mopub Ads
                   'maps.D': 'skyblue', # Google Maps
                   'maps.ad.ay$a': 'skyblue', # Google Maps
                   'drumpadmachine.ui.Pad': 'red', # Game image element
                  }


def parse_labels(hier, d):
    checked = False
    for element_name in ELEMENT_COLOR.keys():
        if hier['name'].count(element_name) > 0:
            except_occur = False
            for element_except in ELEMENT_EXCEPT:
                if hier['resource_id'] is not None and hier['resource_id'].count(element_except) > 0:
                    except_occur = True
                    break
            if not except_occur:
                d[element_name] += 1
                checked = True
            break 

    if not checked and hier['resource_id'] is not None:
        for element_name in ELEMENT_COLOR.keys():
            if hier['resource_id'].count(element_name) > 0:
                except_occur = False
                for element_except in ELEMENT_EXCEPT:
                    if hier['resource_id'].count(element_except) > 0:
                        except_occur = True
                        break
                if not except_occur:
                    d[element_name] += 1
                break
    #
    # Some non-standard layout/views which can't be handled by name/resource-id,
    # they should be processed using full_name(class information).
    #
    full_name_checked = False
    for full_name in FULL_NAME_COLOR.keys():
        if hier['full_name'].count(full_name) > 0 and hier['visible']:
            d[full_name] += 1
    # Recursion
    if hier['children'] is not None:
        for child in hier['children']:
            parse_labels(child, d)
            
            
def draw(hier, img, FILE_NAME, d):
    #
    # Some non-standard layout/views, they don't have standard name.
    # Therefore, we have to guess the label using their name and resource-id.
    #
    checked = False
    for element_name in ELEMENT_COLOR.keys():
        if hier['name'].count(element_name) > 0:
            except_occur = False
            for element_except in ELEMENT_EXCEPT:
                if hier['resource_id'] is not None and hier['resource_id'].count(element_except) > 0:
                    except_occur = True
                    break
            if not except_occur:
                hier['name'] = element_name
                checked = True
            break

    if not checked and hier['resource_id'] is not None:
        for element_name in ELEMENT_COLOR.keys():
            if hier['resource_id'].count(element_name) > 0:
                except_occur = False
                for element_except in ELEMENT_EXCEPT:
                    if hier['resource_id'].count(element_except) > 0:
                        except_occur = True
                        break
                if not except_occur:
                    hier['name'] = element_name
                break

    #
    # Some non-standard layout/views which can't be handled by name/resource-id,
    # they should be processed using full_name(class information).
    #
    full_name_checked = False
    for full_name in FULL_NAME_COLOR.keys():
        if hier['full_name'].count(full_name) > 0 and hier['visible']:
            full_name_checked = True
            b = hier['bounds']
            try:
                d[full_name] += 1
                block = Image.new('RGBA', (b[2] - b[0], b[3] - b[1]), FULL_NAME_COLOR[full_name])
                #print(b[2],  b[0], b[2] - b[0])
                # if ((b[2] - b[0]) > 1440) | ((b[3] - b[1]) > 2560):
                #     print('smth wrong')
                mask_im = Image.new("1", (b[2] - b[0], b[3] - b[1]), 1)
                draw2 = ImageDraw.Draw(mask_im)
                s = 5
                draw2.rectangle([(s, s), (b[2] - b[0] - s, b[3] - b[1] - s)], fill=0)
                img.paste(block, (b[0], b[1]), mask_im)
                if ((b[2] - b[0]) * (b[3] - b[1]))/(SCREEN_SIZE[0] * SCREEN_SIZE[1]) > 0.8:
                    print(FILE_NAME + ":" + full_name + ":Too large:")# + str(((b[2] - b[0]) * (b[3] - b[1]))/(SCREEN_SIZE[0] * SCREEN_SIZE[1])))
            except ValueError:
                pass

    # Coloring
    if not full_name_checked and hier['name'] in ELEMENT_COLOR.keys() and hier['visible']:
        b = hier['bounds']
        try:
            d[hier['name']] += 1
            #print(hier['name'], b, ELEMENT_COLOR[hier['name']])
            block = Image.new('RGBA', (b[2] - b[0], b[3] - b[1]), ELEMENT_COLOR[hier['name']])
            img.paste(block, (b[0], b[1]))
            # if ((b[2] - b[0]) > 1440) | ((b[3] - b[1]) > 2560):
            #     print('smth wrong')
            mask_im = Image.new("1", (b[2] - b[0], b[3] - b[1]), 1)
            draw2 = ImageDraw.Draw(mask_im)
            s = 5
            draw2.rectangle([(s, s), (b[2] - b[0] - s, b[3] - b[1] - s)], fill=0)
            img.paste(block, (b[0], b[1]), mask_im)
            #print(b[2],  b[0], b[2] - b[0])
            if ((b[2] - b[0]) * (b[3] - b[1])) / (SCREEN_SIZE[0] * SCREEN_SIZE[1]) > 0.8:
                print(FILE_NAME + ":" + hier['name'] + ":Too large:")# + str(((b[2] - b[0]) * (b[3] - b[1])) / (SCREEN_SIZE[0] * SCREEN_SIZE[1])))
        except ValueError:
            pass

    # Recursion
    if hier['children'] is not None:
        for child in hier['children']:
            draw(child, img, FILE_NAME, d)
            

class element(object):
    def __init__(self, hier):
        if hier.__class__ != dict:
            self.visible = False
            return
        self.visible = hier['visible-to-user']
        self.clickable = hier['clickable']
        self.bounds = hier['bounds']
        self.name = hier['class'].split('.')[-1]
        self.full_name = hier['class']
        self.scrollable = {'horizontal': hier['scrollable-horizontal'],
                           'vertical': hier['scrollable-vertical']}
        self.resource_id = hier['resource-id'].split('/')[-1] if 'resource-id' in hier else None
        self.text = hier['text'] if 'text' in hier else None
        self.children = [element(i) for i in hier['children']] if 'children' in hier else list()
        # Exception postprocess
        # - if children is invisible, delete it
        wait_del = list()
        if self.children is not None:
            for child in self.children:
                if not child.visible:
                    wait_del.append(child)

        for it in wait_del:
            self.children.remove(it)

        # Exception postprocess
        # - if DrawerLayout has 2+ layout/views (which means, drawer has opened),
        #   delete original layout/view (which priors to the drawer view)
        if self.name.count("DrawerLayout") and len(self.children) > 1:
            self.children.remove(self.children[0])

        # Exception postprocess
        # - if SlidingMenu has 2+ layout/views (which means, slide has opened),
        #   delete original layout/view (which priors to the slide view)
        if self.name == "SlidingMenu" and len(self.children) > 1:
            self.children.remove(self.children[1])

        # Exception postprocess
        # - if element's width/height is under 0 (which is confusing),
        #   delete the element
        if self.children is not None:
            for child in self.children:
                if (child.bounds[2] - child.bounds[0]) < 0 or (child.bounds[3] - child.bounds[1]) < 0:
                    self.children.remove(child)

        # Exception postprocess
        # - if FanView has 2+ layout/views (which means, fan has opened),
        #   delete original layout/view (which priors to the slide view)
        if self.name == "FanView" and len(self.children[0].children) > 1:
            self.children[0].children = [self.children[0].children[0]]

    def __str__(self):
        out = '{' \
              + ("visible: %s, " % self.visible) \
              + ("clickable: %s, " % self.clickable) \
              + ("bounds: %s, " % self.bounds) \
              + ("name: '%s', " % self.name) \
              + ("full_name: '%s', " % self.full_name) \
              + ("scrollable: %s, " % self.scrollable) \
              + ("resource_id: %s, " % ("'" + self.resource_id + "'" if self.resource_id is not None else "None")) \
              + ("text: %s" % ("'" + self.text + "'" if self.text is not None else "None")) \
              + ("children: %s" % self.children) \
              + '}'

        return out

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        out = {'visible': self.visible,
               'clickable': self.clickable,
               'bounds': self.bounds,
               'name': self.name,
               'full_name': self.full_name,
               'scrollable': self.scrollable,
               'resource_id': self.resource_id,
               'text': self.text,
               'children': [child.to_dict() for child in self.children] if self.children is not None else None}

        return out
    
colour_dict = {'BACKGROUND': (255, 255, 153),
               'IMAGE': (96, 96, 96),
               'PICTOGRAM': (255, 0, 0),
               'BUTTON': (0, 255, 0), 
               'TEXT': (0, 0, 255), 
               'LABEL': (102, 255, 201), 
               'CONTAINER': (255, 0, 255), 
               'TEXT_INPUT': (102, 0, 0), 
               'MAP': (255, 153, 153),
               'CHECK_BOX': (153, 76, 0),
               'SWITCH': (255, 178, 102),
               'PAGER_INDICATOR': (153, 153, 0),
               'SLIDER': (255, 255, 102),
               'RADIO_BUTTON': (0, 204, 204),
               'SPINNER': (102, 255, 255),
               'PROGRESS_BAR': (102, 178, 255),
               'ADVERTISEMENT': (76, 0, 153),
               'DRAWER': (178, 102, 255),
               'NAVIGATION_BAR': (153, 0, 153),
               'CARD_VIEW': (255, 102, 255),
               'CONTAINER': (204, 0, 102),
               'DATE_PICKER': (51, 255, 153),
               'NUMBER_STEPPER': (204, 204, 0),
               'TOOLBAR': (255, 128, 0),
               'LIST_ITEM': (0, 0, 0), 
                }


def plot_img_from_tf(raw_dataset, colour_dict = colour_dict, label_to_plot = 'all', N = -1):
    if N == -1:
        N = random.randint(0, 44629)
    print(N)
    for raw_record in raw_dataset.skip(N).take(1):
        ex = tf.train.Example()
        ex.ParseFromString(raw_record.numpy())
        result = {}
        # example.features.feature is the dictionary
        for key, feature in ex.features.feature.items():
          # The values are the Feature objects which contain a `kind` which contains:
          # one of three fields: bytes_list, float_list, int64_list

            kind = feature.WhichOneof('kind')
            result[key] = np.array(getattr(feature, kind).value)
            
        # if result['image/to_drop'] == 1:
        #     print('SHOULD BE DROPPED')

        img_name = result['image/filename'][0].decode('UTF-8')
        print(img_name)

        img = Image.open(f'/Users/danil/Documents/github/clay/jpg/{img_name}')
        plt.figure(figsize=(15, 10))
        #plt.imshow(im);

        if label_to_plot != 'all':
            colour_dict = {element : (0, 0, 0) for element in colour_dict.keys()}
            
            if isinstance(label_to_plot, str):
                colour_dict[label_to_plot] = (255, 0, 0)
                
            elif isinstance(label_to_plot, list):            
                for elem in label_to_plot:
                    colour_dict[elem] = (255, 0, 0)
                
                
        for ind, element in enumerate(result['image/object/class/text']):
            #print(element.decode('UTF-8'))
            b = result['image/object/bbox/xmin'][ind], result['image/object/bbox/ymin'][ind],  \
                result['image/object/bbox/xmax'][ind], result['image/object/bbox/ymax'][ind]

            w, h = img.size
            b = b[0] * w, b[1]*h, b[2]*w, b[3]*h
            b = list(map(int, b))
            block = Image.new('RGBA', (b[2] - b[0], b[3] - b[1]), colour_dict[element.decode('UTF-8')])
            #img.paste(block, (b[0], b[1]))
            # if ((b[2] - b[0]) > 1440) | ((b[3] - b[1]) > 2560):
            #     print('smth wrong')
            mask_im = Image.new("1", (b[2] - b[0], b[3] - b[1]), 1)
            draw2 = ImageDraw.Draw(mask_im)
            s = 5
            draw2.rectangle([(s, s), (b[2] - b[0] - s, b[3] - b[1] - s)], fill=0)
            img.paste(block, (b[0], b[1]), mask_im)

        founded_elements = Counter(result['image/object/class/text'])
        print(founded_elements)

        founded_elements = [i.decode('UTF-8') for i in founded_elements]

        patches = [ mpatches.Patch(color=[j/255 for j in colour_dict[i]], label=f"Level {i}") for i in founded_elements ]

        plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )

        plt.imshow(img);
        return img_name.split('.')[0]
    
    
def plot_img_raw_dataset(N = 0):
    if N == 0:
        N = random.randint(0, 66246)
        
    print(N)
    im = Image.open(f'/Users/danil/Documents/github/clay/image/{N}.jpg')

    f = open(f'/Users/danil/Documents/github/clay/combined/{N}.json')
    data = json.load(f)
    hierarchy = element(data['activity']['root']).to_dict()
    
    img = Image.new('RGBA', SCREEN_SIZE, 'white')
    d = defaultdict(int)
    draw(hierarchy, img, str(N), d)
    img = img.resize(im.size)
    print(d)
    
    fig, axs = plt.subplots(1, 2, figsize=(15, 20))
    axs[0].imshow(im);
    #axs[2].imshow(img);
    axs[1].imshow(im);
    axs[1].imshow(img, alpha = 0.5);
