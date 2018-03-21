import configparser


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('./config.ini', encoding='utf-8-sig')

    def getConfAttr(self, attrName):
        return self.config.get('instruments', attrName)


# # update existing value
# config.set('section_a', 'string_val', 'world')



# # add a new section and some values
# config.add_section('section_b')
# config.set('section_b', 'meal_val', 'spam')
# config.set('section_b', 'not_found_val', 404)

# save to a file
# with open('test_update.ini', 'w') as configfile:
#     config.write(configfile)

