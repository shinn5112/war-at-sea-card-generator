import os
import json
import argparse

from PIL import ImageDraw
from textwrap import wrap

from card_generator.models.assets import *
from card_generator.models.alliance import Alliance
from card_generator.utils.helper_functions import *
from card_generator.models.utils import load_json
from card_generator.models.nation import Nation
from card_generator.models.unit import Unit, UnitType


class Generator:
    """
    Card generator for a single unit.
    """

    def __init__(self, nation: Nation, unit: Unit) -> None:
        self.nation = nation
        self.unit = unit
        if self.nation.get_alliance() == Alliance.Allies.value:
            self.card_base = Image.open(Background.ALLIES_BASE).convert("RGBA")
        else:
            self.card_base = Image.open(Background.AXIS_BASE).convert("RGBA")

    def generate(self, display: bool = False, output_folder: str = None) -> None:
        """
        Generate the card for the current unit.
        :param display: if set to true, will display the card instead of writing it out as an image. Defaults to false.
        :param output_folder: folder to dump the cards to, defaults to the current directory.
        """
        print("{}/{}".format(self.nation.name, self.unit.name))
        y_offset = Values.ATTACK_RECTANGLE_START_Y
        base_draw_layer = ImageDraw.Draw(self.card_base, "RGBA")
        blueprint_layer = Image.new("RGBA", self.card_base.size, Colors.TRANSPARENT)
        transparent_overlay = Image.new("RGBA", self.card_base.size, Colors.TRANSPARENT)
        transparent_overlay_draw = ImageDraw.Draw(transparent_overlay)
        top_overlay = Image.new("RGBA", self.card_base.size, Colors.TRANSPARENT)
        top_overlay_draw = ImageDraw.Draw(top_overlay)

        def populate_header():
            self.card_base.paste(get_emblem(self.nation), Coordinates.NATION_EMBLEM,
                                 get_emblem(self.nation))

            ship_name_font = get_header_font(self.unit.name, tracking=Values.SHIP_NAME_FONT_TRACKING)
            ship_name_y = y_center_text(Values.SHIP_NAME_END_Y,
                                        Values.SHIP_NAME_START_Y,
                                        self.unit.name, ship_name_font
                                        )

            draw_text_psd_style(base_draw_layer,
                                (Values.SHIP_NAME_START_X, ship_name_y),
                                self.unit.name,
                                ship_name_font,
                                tracking=Values.SHIP_NAME_FONT_TRACKING, leading=0, fill=Colors.SHIP_NAME)

            draw_text_psd_style(base_draw_layer,
                                center_text(Coordinates.POINT_CIRCLE_CENTER, str(self.unit.points), Fonts.POINT_VALUE),
                                str(self.unit.points),
                                Fonts.POINT_VALUE,
                                tracking=-100, leading=0, center_x=True, fill=Colors.POINT_VALUE)

            base_draw_layer.text(Coordinates.SHIP_TYPE, self.unit.type,
                                 font=Fonts.SHIP_TYPE_AND_YEAR,
                                 fill=Colors.SHIP_TYPE_AND_YEAR)

            base_draw_layer.text(Coordinates.SHIP_YEAR, str(self.unit.year),
                                 font=Fonts.SHIP_TYPE_AND_YEAR,
                                 fill=Colors.SHIP_TYPE_AND_YEAR)

            base_draw_layer.text(Coordinates.SHIP_SPEED, "Speed - {}".format(self.unit.speed),
                                 font=Fonts.SHIP_SPEED,
                                 fill=Colors.STATS)

            if self.unit.flagship is not None:
                transparent_overlay.paste(Icons.FLAGSHIP, Coordinates.FLAGSHIP)
                transparent_overlay_draw.text(
                    (x_center_text(
                        Coordinates.FLAGSHIP[0], Coordinates.FLAGSHIP[0] + Values.FLAGSHIP_CENTER_OFFSET,
                        str(self.unit.flagship),
                        Fonts.FLAGSHIP
                    ),
                     Values.FLAGSHIP_VALUE_Y
                    ),
                    str(self.unit.flagship),
                    font=Fonts.FLAGSHIP,
                    fill=Colors.BLACK
                )

            if self.unit.planes is not None:
                offset = Values.CARRIER_START_X
                for carrier in range(self.unit.planes):
                    transparent_overlay.paste(Icons.CARRIER, (offset, Values.CARRIER_Y))
                    offset += Values.CARRIER_ICON_SPACING

            # silhouette
            if self.unit.ship_class is not None:
                silhouette = get_silhouette(UnitType.SHIP, self.nation.name, self.unit.ship_class.lower())
                w, h = silhouette.size
                scale = (380 + 150) / w
                silhouette = silhouette.resize((int(w * scale), int(h * scale)))
                w, h = silhouette.size
                transparent_overlay.paste(silhouette, (65 - 45, 97 - h))
            else:
                silhouette = get_silhouette(UnitType.PLANE, self.nation.name, self.unit.name.lower())
                w, h = silhouette.size
                scale = 95 / h
                silhouette = silhouette.resize((int(w * scale), int(h * scale)))
                height = center_image(0, 0, 0, 100, silhouette)[1]
                transparent_overlay.paste(silhouette, (65, height))

        def populate_attack():
            nonlocal y_offset
            # blueprint first
            blueprint = get_blueprint(UnitType.SHIP, self.nation.name, self.unit.ship_class.lower())
            w, h = blueprint.size
            scale = 380 / w
            blueprint = blueprint.resize((int(w * scale), int(h * scale)))
            blueprint_layer.paste(blueprint, (350, center_image(0, y_offset, 0,
                                                                y_offset - 10 + (Values.ATTACK_RECTANGLE_WIDTH *
                                                                                 self.unit.get_attacks()[0]),
                                                                blueprint)[1]))
            draw_text_psd_style(base_draw_layer,
                                Coordinates.ATTACK_HEADING,
                                "Attacks",
                                font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                                tracking=-50, leading=0, center_x=True, fill=Colors.STATS)

            base_draw_layer.text(Coordinates.ATTACK_RANGE_HEADING_0, "0",
                                 font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                                 fill=Colors.STATS)

            base_draw_layer.text(Coordinates.ATTACK_RANGE_HEADING_1, "1",
                                 font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                                 fill=Colors.STATS)

            base_draw_layer.text(Coordinates.ATTACK_RANGE_HEADING_2, "2",
                                 font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                                 fill=Colors.STATS)

            base_draw_layer.text(Coordinates.ATTACK_RANGE_HEADING_3, "3",
                                 font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                                 fill=Colors.STATS)

            base_draw_layer.line(Coordinates.ATTACK_HEADING_DIVIDER, Colors.STATS, Values.BORDER_WIDTH)
            base_draw_layer.line(Coordinates.ATTACK_HEADING_DIVIDER_1, Colors.STATS, 1)
            base_draw_layer.line(Coordinates.ATTACK_HEADING_DIVIDER_2, Colors.POINT_VALUE, 1)
            base_draw_layer.line(Coordinates.ATTACK_HEADING_DIVIDER_3, Colors.POINT_VALUE, 1)

            number_of_attacks, attacks = self.unit.get_attacks()
            for i in range(number_of_attacks):
                # attack icon and box
                icon = get_attack_icon(attacks[i]["name"])
                current_attack = attacks[i]["value"]
                transparent_overlay_draw.rectangle(
                    (
                        (Values.LEFT_CARD_BORDER, y_offset + 2),
                        (Values.ATTACK_RECTANGLE_START_X, y_offset + Values.ATTACK_RECTANGLE_WIDTH)
                    ),
                    Colors.BLACK, None, 0)
                # attack icons
                top_overlay.paste(icon, center_image(Values.LEFT_CARD_BORDER,
                                                     y_offset,
                                                     Values.ATTACK_RECTANGLE_START_X,
                                                     y_offset +
                                                     Values.ATTACK_RECTANGLE_WIDTH + 4,
                                                     icon
                                                     )
                                  )

                # green transparent background
                transparent_overlay_draw.rectangle(
                    (
                        (Values.ATTACK_RECTANGLE_START_X, y_offset + 1),
                        (Values.ATTACK_RECTANGLE_END_X, y_offset + Values.ATTACK_RECTANGLE_WIDTH)
                    ),
                    Colors.ATTACK_VALUE_BACKGROUND, None, 0)
                # attack vertical dividers
                transparent_overlay_draw.line(
                    [
                        (Values.ATTACK_VERTICAL_DIVIDER_1, y_offset + 1),
                        (Values.ATTACK_VERTICAL_DIVIDER_1, y_offset + Values.ATTACK_RECTANGLE_WIDTH)
                    ],
                    Colors.BLACK, 1)
                transparent_overlay_draw.line(
                    [
                        (Values.ATTACK_VERTICAL_DIVIDER_2, y_offset + 1),
                        (Values.ATTACK_VERTICAL_DIVIDER_2, y_offset + Values.ATTACK_RECTANGLE_WIDTH)
                    ],
                    Colors.BLACK, 1)
                transparent_overlay_draw.line(
                    [
                        (Values.ATTACK_VERTICAL_DIVIDER_3, y_offset + 1),
                        (Values.ATTACK_VERTICAL_DIVIDER_3, y_offset + Values.ATTACK_RECTANGLE_WIDTH)
                    ],
                    Colors.BLACK, 1)

                # render the attacks
                for attack_range in range(4):
                    # dynamically find the size of the attack value text, so it can be centered
                    w, h = transparent_overlay_draw.textsize(current_attack[attack_range], font=Fonts.ATTACK_STATS)
                    current_x_middle = Values.ATTACK_RECTANGLE_START_X + (Values.DIVIDER_SPACING / 2) \
                                       + (attack_range * Values.DIVIDER_SPACING)
                    current_y_middle = y_offset - 5 + (Values.ATTACK_RECTANGLE_WIDTH / 2)

                    transparent_overlay_draw.text(
                        (
                            current_x_middle - (w / 2),
                            current_y_middle - (h / 2)
                        ),
                        current_attack[attack_range],
                        font=Fonts.ATTACK_STATS,
                        fill=Colors.STATS)

                if i == 0:
                    # no horizontal border needed
                    pass
                else:
                    # attack icon dividers
                    transparent_overlay_draw.line(
                        [
                            (Values.LEFT_CARD_BORDER, y_offset + 1),
                            (Values.ATTACK_RECTANGLE_START_X, y_offset + 1)
                        ],
                        Colors.WHITE, 1)
                    # black horizontal grid lines
                    transparent_overlay_draw.line(
                        [
                            (Values.ATTACK_RECTANGLE_START_X, y_offset + 1),
                            (Values.ATTACK_RECTANGLE_END_X, y_offset + 1)
                        ],
                        Colors.BLACK, 1)
                y_offset += Values.ATTACK_RECTANGLE_WIDTH

            # black line outer border
            transparent_overlay_draw.line(
                [
                    (Values.ATTACK_RECTANGLE_END_X, Values.ATTACK_HEADER_Y_END),
                    (Values.ATTACK_RECTANGLE_END_X, y_offset + 1)
                ],
                Colors.BLACK, Values.BORDER_WIDTH)
            # white line inner border
            transparent_overlay_draw.line(
                [
                    (Values.ATTACK_RECTANGLE_START_X, Values.ATTACK_HEADER_Y_END),
                    (Values.ATTACK_RECTANGLE_START_X, y_offset + 1)
                ],
                Colors.POINT_VALUE, Values.BORDER_WIDTH)
            # bottom grey border
            transparent_overlay_draw.line(
                [
                    (Values.LEFT_CARD_BORDER, y_offset + 1),
                    (Values.ATTACK_RECTANGLE_END_X + 1, y_offset + 1)
                ],
                Colors.LIGHT_GREY, Values.BORDER_WIDTH)

        def populate_armor():
            transparent_overlay_draw.rectangle(
                (
                    (Values.LEFT_CARD_BORDER, y_offset + Values.ARMOR_ROW_TOP_MARGIN),
                    (Values.LEFT_CARD_BORDER + Values.ARMOR_ROW_WIDTH,
                     y_offset + Values.ARMOR_ROW_TOP_MARGIN + Values.ARMOR_ROW_HEIGHT)
                ),
                Colors.BLACK, None, 0)
            # Armor box upper border
            transparent_overlay_draw.line(
                [
                    (Values.LEFT_CARD_BORDER, y_offset + Values.ARMOR_ROW_TOP_MARGIN),
                    (Values.LEFT_CARD_BORDER + Values.ARMOR_ROW_WIDTH, y_offset + Values.ARMOR_ROW_TOP_MARGIN)
                ],
                Colors.DARK_GREY, Values.BORDER_WIDTH)

            # Armor box lower border
            transparent_overlay_draw.line(
                [
                    (Values.LEFT_CARD_BORDER, y_offset + Values.ARMOR_ROW_TOP_MARGIN + Values.ARMOR_ROW_HEIGHT),
                    (Values.LEFT_CARD_BORDER + Values.ARMOR_ROW_WIDTH,
                     y_offset + Values.ARMOR_ROW_TOP_MARGIN + Values.ARMOR_ROW_HEIGHT)
                ],
                Colors.LIGHT_GREY, Values.BORDER_WIDTH)

            # Armor stats headings
            x_offset = Values.LEFT_CARD_BORDER

            armor_values = self.unit.get_armor()
            for entry in ["ARMOR", "VITAL ARMOR", "HULL POINTS"]:
                # dynamically find the size of the attack text, so it can be centered
                w, h = transparent_overlay_draw.textsize(entry, font=Fonts.ATTACK_ARMOR_STATS_HEADINGS)
                current_y_middle = y_offset + Values.ARMOR_ROW_TOP_MARGIN + (Values.ARMOR_ROW_HEIGHT / 2) - 3
                transparent_overlay_draw.text(
                    (
                        x_offset + Values.ARMOR_TEXT_LEFT_MARGIN,
                        current_y_middle - (h / 2)
                    ),
                    entry,
                    font=Fonts.ATTACK_ARMOR_STATS_HEADINGS,
                    fill=Colors.STATS)
                x_offset += w + Values.ARMOR_TEXT_LEFT_MARGIN + Values.ARMOR_TEXT_RIGHT_MARGIN
                # Add a box for the values
                top_overlay.paste(Background.HIT_POINTS, (x_offset, y_offset + Values.ARMOR_ROW_TOP_MARGIN + 1))
                top_overlay_draw.text(
                    center_text(
                        x_offset,
                        y_offset + Values.ARMOR_ROW_TOP_MARGIN - 6,
                        x_offset + 44,
                        y_offset + Values.ARMOR_ROW_TOP_MARGIN + 45,
                        armor_values[entry],
                        Fonts.ARMOR_STATS),
                    armor_values[entry],
                    font=Fonts.ARMOR_STATS,
                    fill=Colors.BLACK
                )
                x_offset += 44

        def populate_abilities():
            nonlocal y_offset
            current_y_offset = y_offset
            correct_size = False
            font_size = 25
            # dry run until we get the right size
            while not correct_size:
                abilities = ImageFont.truetype(Fonts.get_abilities_font(), font_size)
                abilities_title = ImageFont.truetype(Fonts.get_abilities_title_font(), font_size)
                y_offset = current_y_offset + Values.ARMOR_ROW_TOP_MARGIN + 45 + Values.SPECIAL_ABILITY_TOP_MARGIN
                for title, ability in sorted(self.unit.special_abilities.items(), key=ability_sort):
                    if ability is not None:
                        title = title + " - "
                    first_line_offset = abilities_title.getsize(title)[0]
                    # scale the width of the first line to accommodate the title text.
                    first_line_width = int(
                        (1.2 - ((
                                        Values.SPECIAL_ABILITY_LEFT_MARGIN + first_line_offset) / Values.ATTACK_RECTANGLE_END_X)) *
                        (Values.SPECIAL_ABILITY_TEXT_WIDTH * (25 / font_size)))
                    text = ability
                    if ability is not None:
                        if first_line_width > 0:
                            text = wrap(text, width=first_line_width)
                            first_line = text[0]
                            text = " ".join(text[1:])
                            y_offset += abilities.getsize(first_line)[1]
                        else:
                            y_offset += abilities.getsize(title)[1]
                        for line in wrap(text, width=int((Values.SPECIAL_ABILITY_TEXT_WIDTH * (25 / font_size)))):
                            y_offset += abilities.getsize(line)[1]
                    else:
                        y_offset += abilities_title.getsize(title)[1]
                    y_offset += Values.SPECIAL_ABILITY_BOTTOM_MARGIN
                if y_offset < 980:
                    correct_size = True
                else:
                    font_size -= 1

            # real run
            y_offset = current_y_offset + Values.ARMOR_ROW_TOP_MARGIN + 45 + Values.SPECIAL_ABILITY_TOP_MARGIN
            abilities = ImageFont.truetype(Fonts.get_abilities_font(), font_size)
            abilities_title = ImageFont.truetype(Fonts.get_abilities_title_font(), font_size)
            for title, ability in sorted(self.unit.special_abilities.items(), key=ability_sort):
                if ability is not None:
                    title = title + " - "
                transparent_overlay_draw.text((Values.SPECIAL_ABILITY_LEFT_MARGIN, y_offset), title,
                                              font=abilities_title,
                                              fill=Colors.WHITE)
                first_line_offset = abilities_title.getsize(title)[0]
                # scale the width of the first line to accommodate the title text.
                first_line_width = int(
                    (1.2 - ((Values.SPECIAL_ABILITY_LEFT_MARGIN + first_line_offset) / Values.ATTACK_RECTANGLE_END_X)) *
                    (Values.SPECIAL_ABILITY_TEXT_WIDTH * (25 / font_size)))
                text = ability
                if ability is not None:
                    if first_line_width > 0:
                        text = wrap(text, width=first_line_width)
                        first_line = text[0]
                        text = " ".join(text[1:])
                        transparent_overlay_draw.text(
                            (Values.SPECIAL_ABILITY_LEFT_MARGIN + first_line_offset, y_offset),
                            first_line,
                            font=abilities, fill=Colors.WHITE)
                        y_offset += abilities.getsize(first_line)[1]
                    else:
                        y_offset += abilities.getsize(title)[1]
                    for line in wrap(text, width=int((Values.SPECIAL_ABILITY_TEXT_WIDTH * (25 / font_size)))):
                        transparent_overlay_draw.text((Values.SPECIAL_ABILITY_LEFT_MARGIN, y_offset), line,
                                                      font=abilities, fill=Colors.WHITE)
                        y_offset += abilities.getsize(line)[1]
                else:
                    y_offset += abilities_title.getsize(title)[1]
                y_offset += Values.SPECIAL_ABILITY_BOTTOM_MARGIN

        def populate_set():
            set_offset = Values.LEFT_CARD_BORDER
            transparent_overlay.paste(get_set_icon(self.unit.set),
                                      (set_offset, Values.SET_Y_OFFSET),
                                      get_set_icon(self.unit.set)
                                      )

            set_offset += get_set_icon(self.unit.set).size[0]
            base_draw_layer.text((set_offset + 10, Values.SET_Y_OFFSET - 2), self.unit.set_number, font=Fonts.SET_INFO,
                                 fill=Colors.WHITE)
            set_offset += Fonts.SET_INFO.getsize(self.unit.set_number)[0] + 18

            if get_rarity_icon(self.unit.rarity) is not None:
                transparent_overlay.paste(get_rarity_icon(self.unit.rarity),
                                          (set_offset, Values.SET_Y_OFFSET),
                                          get_rarity_icon(self.unit.rarity)
                                          )

        populate_header()
        populate_attack()
        populate_armor()
        populate_abilities()
        populate_set()
        out = Image.alpha_composite(transparent_overlay, top_overlay)
        out = Image.alpha_composite(blueprint_layer, out)
        out = Image.alpha_composite(self.card_base, out)
        if display:
            out.show()
        if output_folder is not None:
            card_path = (os.path.join(output_folder, "cards", self.nation.name))
        else:
            card_path = (os.path.join(os.getcwd(), "cards", self.nation.name))
        try:
            out.save("{}/{}.png".format(card_path, self.unit.name).replace("\"", ";"))
            print("saved to {}".format(card_path))
        except FileNotFoundError:
            os.makedirs(card_path, exist_ok=True)
            out.save("{}/{}.png".format(card_path, self.unit.name).replace("\"", ";"))


def generate_all(output_folder: str = None):
    """
    Generates all units that are present in the included War at Sea data file.
    :param output_folder: folder to dump the cards to, defaults to the current directory.
    """
    data_file = get_war_at_sea_json()
    data = json.load(data_file)
    axis_and_allies_deck = load_json(data)
    for nation in axis_and_allies_deck:
        for unit in nation.get_units():
            Generator(nation, unit).generate(output_folder=output_folder)
    data_file.close()


def generate_country(country: str, output_folder: str = None):
    """
    Generates all units for a given country.
    :param country: name of the nation to generate units for.
    :param output_folder: folder to dump the cards to, defaults to the current directory.
    """
    data_file = get_war_at_sea_json()
    data = json.load(data_file)
    axis_and_allies_deck = load_json(data)
    try:
        index = 0
        for candidate_country in axis_and_allies_deck:
            if candidate_country.name == country:
                break
            else:
                index += 1
        if index == len(axis_and_allies_deck):
            raise ValueError("\"{}\" does not exist in the default countries".format(country))
        for unit in axis_and_allies_deck[index].get_units():
            Generator(axis_and_allies_deck[index], unit).generate(output_folder=output_folder)
    except ValueError as e:
        print(e)


# TODO make this more friendly.
def generate_single(self):
    data_file = get_war_at_sea_json()
    data = json.load(data_file)
    axis_and_allies_deck = load_json(data)
    Generator(axis_and_allies_deck[1], axis_and_allies_deck[1].get_units()[32]).generate(display=True)
    data_file.close()


if __name__ == '__main__':
    commands = {
        "generate_all": generate_all,
        "generate_country": generate_country
    }

    parser = argparse.ArgumentParser(prog="War at Sea Card Generator",
                                     description="Generate unit cards for the Axis and Allies War at Sea Naval "
                                                 "Miniatures game.")
    subparsers = parser.add_subparsers(dest="command")
    generate_all_command = subparsers.add_parser("generate_all")
    generate_all_command.description = "Generate all units for all countries in the included War at Sea data set."
    generate_all_command.add_argument("-o", "--output-folder",
                                      help="Location to output the generated cards to, defaults to the current "
                                           "directory.")
    generate_country_command = subparsers.add_parser("generate_country")
    generate_country_command.description = "Generate all units for a specific country"
    generate_country_command.add_argument("-c", "--country", required=True,
                                          help="name of the country to generate units for")
    generate_country_command.add_argument("-o", "--output-folder",
                                          help="Location to output the generated cards to, defaults to the current "
                                               "directory.")
    args = parser.parse_args()
    # lookup the command
    command = commands[args.command]
    # store all arguments, then remove the command
    args = vars(args)
    del args["command"]
    # pass all remaining args as keyword args.
    command(**args)
