from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Item, Category

engine = create_engine('sqlite:///hockeyshop.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#---------------------------------
# Populate hockeyshop database
#---------------------------------

# Items in category Jerseys
category1 = Category(name="Jerseys")
session.add(category1)
session.commit()

jersey1 = Item( name="Vancouver Canucks Large Jersey",
                price=12995,
                description="Support your team with this authentic NHL Jersey",
                num_avail=8,
                image="canucks_jersey.jpg",
                category=category1)

session.add(jersey1)
session.commit()

jersey2 = Item( name="Boston Bruins Medium Jersey",
                price=12995,
                description="Looks sharp with this authentic NHL Jersey",
                num_avail=18,
                image="bruins_jersey.jpg",
                category=category1)

session.add(jersey2)
session.commit()

jersey3 = Item( name="San Jose Sharks Small Jersey",
                price=12995,
                description="Cheer on your team in this authentic NHL Jersey",
                num_avail=4,
                image="",
                category=category1)

session.add(jersey3)
session.commit()

jersey4 = Item( name="Edmonton Oilers Large Jersey",
                price=12995,
                description="Show you're a real fan with this authentic NHL Jersey",
                num_avail=34,
                image="oilers_jersey.jpg",
                category=category1)

session.add(jersey4)
session.commit()

# Items in category skates
category2 = Category(name="Skates")
session.add(category2)
session.commit()

skate1 = Item(  name="Bauer Supreme 180",
                price=49999,
                description="Bauer Supreme 180 Skates improve your skills on the ice thanks to a hydrophobic grip liner, lightweight Anaform ankle pads and a FORM-FIT footbed with stabilizer grip. These skates include a thermoformable full upper, pro TPR outsole and TUUK LIGHTSPEED EDGE blade holder, as well.",
                num_avail=2,
                image="SUPREME180Skate_main.png",
                category=category2)

session.add(skate1)
session.commit()

skate2 = Item(  name="Bauer Vapor x9000",
                price=19999,
                description="Be a true difference maker with the VAPOR X900 skates. Break to the net faster, and win the race to loose pucks with the 3D lasted Curv composite upper with X-rib pattern and full lightweight composite outsole. Plus change your steel on the fly with the TUUK LIGHTSPEED EDGE.",
                num_avail=6,
                image="sk_1045923_900x_main.png",
                category=category2)

session.add(skate2)
session.commit()

skate3 = Item(  name="Bauer Nexus 8000",
                price=32999,
                description="Stop, turn and get more explosive strides with the skate that gives you better control. Plus the LIGHTSPEED EDGE Holder lets you change steel in seconds, so you'll always be ready to control the game.",
                num_avail=7,
                image="nexus8000.jpg",
                category=category2)

session.add(skate3)
session.commit()

# Items in category sticks
category3 = Category(name="Sticks")
session.add(category3)
session.commit()

stick1 = Item(  name="Bauer Vapor 1X",
                price=6795,
                description="The most advanced VAPOR stick yet. Designed to hit your mark faster than ever before, make a difference on the ice with the new Quick-Release Taper Technology of VAPOR 1X.",
                num_avail=32,
                image="vapor1x.png",
                category=category3)

session.add(stick1)
session.commit()

stick2 = Item(  name="Bauer Supreme Totalone MX3",
                price=12195,
                description="Designed to let you take your hardest shot, the SUPREME TOTALONE MX3 is built for power. With incredible energy transfer from the shaft to the blade, multiply your force and shoot harder than ever before.",
                num_avail=15,
                image="suprememx3.png",
                category=category3)

session.add(stick2)
session.commit()

stick3 = Item(  name="Bauer Nexus 8000",
                price=4395,
                description="Take control with the NEXUS 8000 stick. A new advanced sweet spot gives you more control, more accuracy and ultimately more goals.",
                num_avail=32,
                image="nexus8000.png",
                category=category3)

session.add(stick3)
session.commit()

# items in category goalie pads
category4 = Category(name="Goalie Pads")
session.add(category4)
session.commit()

gpad1 = Item(   name="Bauer Reactor 9000",
                price=13001,
                description="Designed for goalies who rely on their quickness and agility, the REACTOR pads are lightweight, flexible and more durable than ever with the AX SUEDE QUATTRO+ knee landing and leg channel, plus the unique Pro Core insert.",
                num_avail=1,
                image="reactor9000.png",
                category=category4)

session.add(gpad1)
session.commit()

gpad2 = Item(   name="Bauer Supreme One.7",
                price=18054,
                description="Ideal for butterfly-style goalies, the SUPREME ONE.7 features MYFLEX 2.0 which allows goalies to create the optimal flex for their game. An adjustable knee lock can be moved up or down to personalize the fit.",
                num_avail=3,
                image="supremeone7.png",
                category=category4)

session.add(gpad2)
session.commit()
