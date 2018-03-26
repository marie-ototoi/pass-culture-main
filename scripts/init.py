# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask import current_app as app
from pprint import pprint
import traceback

from utils.mock import set_from_mock
from utils.token import get_all_tokens

@app.manager.command
def init():
    try:
        do_init()
    except Exception as e:
        print('ERROR: '+str(e))
        traceback.print_tb(e.__traceback__)
        pprint(vars(e))


def do_init():
    check_and_save = app.model.PcObject.check_and_save
    model = app.model

    ## USERS

    # un jeune client qui veut profiter du pass-culture
    client_user = model.User()
    client_user.publicName = "Arnaud Bétrémieux"
    client_user.account = 100
    client_user.email = "arnaud.betremieux@beta.gouv.fr"
    client_user.setPassword("arnaud123")
    check_and_save(client_user)
    set_from_mock("thumbs", client_user, 1)

    # un acteur culturel qui peut jouer a rajouter des offres
    # dans un petit libraire (a la mano) - un libraire moyen (via e-paging)
    # un conservatoire (via spreadsheet)
    pro_user = model.User()
    pro_user.publicName = "Erwan Ledoux"
    pro_user.email = "erwan.ledoux@beta.gouv.fr"
    pro_user.setPassword("erwan123")
    check_and_save(pro_user)
    set_from_mock("thumbs", pro_user, 2)

    # OFFERERS

    # le petit libraire (à la mano)
    offerer = model.Offerer()
    small_library_offerer = offerer
    offerer.name = "MaBoutique"
    offerer.offerProvider = "OpenAgendaOffers"
    offerer.idAtOfferProvider = "80942872"
    check_and_save(offerer)
    set_from_mock("thumbs", offerer, 1)

    userOfferer = model.UserOfferer()
    userOfferer.rights = "admin"
    userOfferer.user = pro_user
    userOfferer.offerer = offerer
    check_and_save(userOfferer)

    # le libraire moyen (via e-paging)
    try:
        offerer = model.Offerer.query\
                               .filter_by(name="Folies d'encre Aulnay-sous-Bois")\
                               .first_or_404()
        userOfferer = model.UserOfferer()
        userOfferer.offerer = offerer
        userOfferer.rights = "admin"
        userOfferer.user = pro_user
        check_and_save(userOfferer)
    except:
        print("WARNING: If you want to bind the pro user to Folies d'encre Aulnay-sous-Bois, You need to do \'pc update_providables -m\'")

    # le conservatoire (via spreadsheet)
    offerer = model.Offerer()
    offerer.name = "l'Avant Seine / théâtre de Colombes"
    offerer.offerProvider = "Spreadsheet"
    offerer.idAtOfferProvider = "avant_seine.xlsx"
    check_and_save(offerer)
    set_from_mock("spreadsheets", offerer, 1)
    set_from_mock("thumbs", offerer, 2)
    set_from_mock("zips", offerer, 1)

    userOfferer = model.UserOfferer()
    userOfferer.rights = "admin"
    userOfferer.user = pro_user
    userOfferer.offerer = offerer
    check_and_save(userOfferer)

    ## VENUES

    venue_bookshop = model.Venue()
    venue_bookshop.name = "MaBoutique"
    venue_bookshop.address = "75 Rue Charles Fourier, 75013 Paris"
    venue_bookshop.latitude = 48.82387
    venue_bookshop.longitude = 2.35284
    check_and_save(venue_bookshop)

    venue_theater = model.Venue()
    venue_theater.name = "Conservatoire National de la Danse"
    venue_theater.address = "209 Avenue Jean Jaurès, 75019 Paris"
    venue_theater.latitude = 48.8889391
    venue_theater.longitude = 2.3887928
    check_and_save(venue_theater)

    venue_museum = model.Venue()
    venue_museum.name = "Musée d'Orsay"
    venue_museum.address = "1 rue de la Légion d'Honneur, 75007 Paris"
    venue_museum.latitude = 48.8599614
    venue_museum.longitude = 2.3243727
    check_and_save(venue_museum)


    ## CONTENT 1

    thing1 = model.Thing()
    thing1.type = model.ThingType.Book
    thing1.description = "Howard Phillips Lovecraft est sans nul doute l'auteur fantastique le plus influent du xxe siècle. Son imaginaire unique et terrifiant n'a cessé d'inspirer des générationsd'écrivains, de cinéastes, d'artistes ou de créateurs d'univers de jeux, de Neil Gaiman à Michel Houellebecq en passant par Metallica. Le mythe de Cthulhu est au coeur de cette oeuvre : un panthéon de dieux et d'êtres monstrueux venus du cosmos et de la nuit des temps ressurgissent pour reprendre possession de notre monde. Ceux qui en sont témoins sont voués à la folie et à la destruction. Les neuf récits essentiels du mythe sont ici réunis dans une toute nouvelle traduction. À votre tour, vous allez pousser la porte de la vieille bâtisse hantée qu'est la Maison de la Sorcière, rejoindre un mystérieux festival où l'on célèbre un rite impie, découvrir une cité antique enfouie sous le sable, ou échouer dans une ville portuaire dépeuplée dont les derniers habitants sont atrocement déformés.."
    thing1.name = "Cthulhu ; le mythe"
    thing1.type = "Book"
    thing1.identifier = "9782352945536"
    thing1.extraData = {
        'author' : "Howard Phillips Lovecraft",
        'prix_livre' : "25"
    }
    check_and_save(thing1)
    set_from_mock("thumbs", thing1, 1)

    offer1 = model.Offer()
    offer1.offerer = small_library_offerer
    offer1.thing = thing1
    offer1.price = 25
    offer1.venue = venue_bookshop
    check_and_save(offer1)

    mediation1 = model.Mediation()
    mediation1.author = pro_user
    mediation1.backText = "Cthulhu le Mythe, livre I, de H.P. Lovecraft, pour un premier pas dans la littérature… frissons garantis ! Howard Phillips Lovecraft, né le 20 août 1890 à Providence (Rhode Island) et mort le 15 mars 1937 dans la même ville, est un écrivain américain connu pour ses récits fantastiques, d'horreur et de science-fiction."
    mediation1.thing = thing1
    mediation1.what = "Un des trois tomes de Cthulhu le Mythe, au choix"
    check_and_save(mediation1)
    set_from_mock("thumbs", mediation1, 1)

    user_mediation1 = model.UserMediation()
    first_user_mediation = model.UserMediation.query\
                           .filter_by(user=client_user)\
                           .first()
    if first_user_mediation is None:
        user_mediation1.isFirst = True
    user_mediation1.user = client_user
    user_mediation1.validUntilDate = datetime.now() + timedelta(days=2)
    user_mediation1.mediation = mediation1
    check_and_save(user_mediation1)

    umo1 = model.UserMediationOffer()
    umo1.offer = offer1
    umo1.userMediation = user_mediation1
    check_and_save(umo1)

    ## CONTENT 2

    event2 = model.Thing()
    event2.isActive = True
    event2.idAtProviders = 1
    event2.dateModifiedAtLastProvider = '2018-03-05T13:00:00'
    event2.name = "Atelier BD et dédicace avec Joann Sfar à la MC93"
    event2.description = "Atelier d'initiation avec la création d'une page (4 à 6 cases) sur un scénario collectif ou un scénario individuel imaginé par les participants.\n Le créateur du Chat du Rabbin et de Petit Vampire vous attend dans la Maison de la Culture du 93 pour un atelier bande dessinée suivi d’une séance de dédicace."
    event2.lastProviderId = 1
    check_and_save(event2)
    set_from_mock("thumbs", event2, 1)
    #Samedi 10 février  de 14h30 - 17h

    offer2 = model.Offer()
    offer2.offerer = small_library_offerer
    offer2.thing = event2
    offer2.price = 10
    offer2.venue = venue_bookshop
    check_and_save(offer2)

    ## CONTENT 3

    event3 = model.Thing()
    event3.isActive = True
    event3.idAtProviders = 1
    event3.dateModifiedAtLastProvider = '2018-03-05T13:00:00'
    event3.name = "Visite Nocturne"
    event3.description = "Visite guidée de 1h30 du musée pour des groupes de minimum 15 personnes."
    event3.lastProviderId = 1
    check_and_save(event3)
    set_from_mock("thumbs", event3, 3)
    # Tous les vendredis à 22h

    offer3 = model.Offer()
    offer3.offerer = small_library_offerer
    offer3.thing = event3
    offer3.price = 8
    offer3.venue = venue_museum
    check_and_save(offer3)

    mediation3 = model.Mediation()
    mediation3.author = pro_user
    mediation3.backText = "En compagnie d’un accompagnateur, découvrez les dessous d’Orsay lors d’une séance nocturne de 1h30 où le musée est à vous. D’où viennent donc ces dinosaures dans L'angélus de Millet ?"
    mediation3.event = event3
    mediation3.what = "Atelier d'initiation avec la création d'une page (4 à 6 cases) sur un scénario collectif ou un scénario individuel imaginé par les participants."
    check_and_save(mediation3)

    user_mediation3 = model.UserMediation()
    user_mediation3.mediation = mediation3
    user_mediation3.user = client_user
    user_mediation3.validUntilDate = datetime.now() + timedelta(days=2)
    check_and_save(user_mediation3)
    umo3 = model.UserMediationOffer()
    umo3.offer = offer3
    umo3.userMediation = user_mediation3
    check_and_save(umo3)


    ## CONTENT 4

    thing4 = model.Thing()
    thing4.type = model.ThingType.Book
    thing4.description = "Roman d'aventures, écrit par Jules Verne, publié en 1872. Il raconte la course autour du monde d'un gentleman anglais, Phileas Fogg, qui a fait le pari d'y parvenir en 80 jours. Il est accompagné par Jean Passepartout, son serviteur français. L'ensemble du roman est un habile mélange entre récit de voyage (traditionnel pour Jules Verne) et données scientifiques comme celle utilisée pour le rebondissement de la chute du roman."
    thing4.name = "Le Tour du monde en 80 jours (édition enrichie illustrée)"
    thing4.type = "Book"
    thing4.identifier = "2072534054"
    thing4.extraData = {
        'author' : "Jules Verne",
        'prix_livre' : "13.99"
    }
    thing4.thumbCount = 1
    check_and_save(thing4)
    set_from_mock("thumbs", thing4, 4)

    offer4 = model.Offer()
    offer4.offerer = small_library_offerer
    offer4.price = 8
    offer4.venue = venue_bookshop
    offer4.thing = thing4
    check_and_save(offer4)

    mediation4 = model.Mediation()
    mediation4.author = pro_user
    mediation4.backText = "Jules Verne savait-il déjà que le voyage en ballon serait le transport du futur ?"
    mediation4.frontText = "Histoire de voyager sans augmenter son bilan carbone"
    mediation4.thing = thing4

    user_mediation4 = model.UserMediation()
    user_mediation4.mediation = mediation4
    user_mediation4.user = client_user
    user_mediation4.validUntilDate = datetime.now() + timedelta(days=2)
    check_and_save(user_mediation4)
    umo4 = model.UserMediationOffer()
    umo4.offer = offer4
    umo4.userMediation = user_mediation4
    check_and_save(umo4)

    booking4 = model.Booking()
    booking4.user = client_user
    booking4.offer = offer4
    booking4.token = 'FUUEEM'
    booking4.userMediation = user_mediation4
    check_and_save(user_mediation4)
    umb4 = model.UserMediationBooking()
    umb4.booking = booking4
    umb4.userMediation = user_mediation4
    check_and_save(umb4)

    ## CONTENT 5

    event5 = model.Event()
    event5.isActive = True
    event5.idAtProviders = 1
    event5.dateModifiedAtLastProvider = '2018-03-05T13:00:00'
    event5.name = "Visite Nocturne"
    event5.description = "Visite guidée de 1h30 du musée pour des groupes de minimum 15 personnes."
    event5.lastProviderId = 1
    check_and_save(event5)
    set_from_mock("thumbs", event5, 2)
    # Tous les vendredis à 22h

    offer5 = model.Offer()
    offer5.offerer = small_library_offerer
    offer5.thing = event5
    offer5.price = 8
    offer5.venue = venue_museum
    check_and_save(offer5)

    mediation5 = model.Mediation()
    mediation5.author = pro_user
    mediation5.backText = "En compagnie d’un accompagnateur, découvrez les dessous d’Orsay lors d’une séance nocturne de 1h30 où le musée est à vous. D’où viennent donc ces dinosaures dans L'angélus de Millet ?"
    mediation5.event = event3
    mediation5.what = "Atelier d'initiation avec la création d'une page (4 à 6 cases) sur un scénario collectif ou un scénario individuel imaginé par les participants."
    check_and_save(mediation5)

    user_mediation5 = model.UserMediation()
    user_mediation5.mediation = mediation5
    user_mediation5.user = client_user
    user_mediation5.validUntilDate = datetime.now() + timedelta(days=2)
    check_and_save(user_mediation5)

    umo5 = model.UserMediationOffer()
    umo5.offer = offer5
    umo5.userMediation = user_mediation5
    check_and_save(umo5)
