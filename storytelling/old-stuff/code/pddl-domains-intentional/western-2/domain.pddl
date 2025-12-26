;; Western domain Adapted from the following:
;; ------------------------------------------
;;; A domain for modeling stories in the Wild West
;;; Created by Stephen G. Ware
;;; https://www.cs.uky.edu/ ̃sgware/projects/glaive/


(define (domain western-type)
(:requirements :typing :equality :negative-preconditions) 
(:types 
  sickness place item character animal - object
  sheriff rancher son - character
  dairyfarmer - character
  texasranger - character
  valuable - item
  city ranch saloon - place
)

(:intendable
  arrested
  owns
  at
)

(:delegatable 
  arrested
  owns
  at
)

(:constants
  railwaydeveloper - character  
  theCity - place
  town - place
  theFarmer - dairyfarmer
  theSon - son
  theRanger - texasranger
  antivenom - item
  snakebite - sickness
  generalstore - place
  theRanch - ranch
  theFarm - ranch
  theSaloon - saloon
  ranch_place - place
  hank - rancher
  timmy - son
  carl - sheriff
)

(:predicates 
  (theFarmChar ?p - character)
  (theMover ?p - character)
  (theCriminal ?p - character)
  (theInvalid ?p - character)
  (invalid-unwell)
  (invalid-recovered)
  (done-crime ?p - character)
  (crime-done)
  (arrested ?character - character)
  (criminal-arrested)
  (theArrester ?p - character)
  (family ?p1 ?p2 - character)
  (survived-winter)
  (has-axe ?p - character)
  (spring)
  (autumn)
  (winter)
  (prepared-for-winter)
  (has-medicine ?p - character)
  (healthy ?p - character)
  (family-ok)
  (winter-proofed-house)
  (has-firewood ?p - character) 
  (decided-move-city)
  (has-cash ?p - character)
  (wants ?p - character ?l - place)
  (owns ?p - character ?l - place)
  (has-ticket ?p - character)
  (moved-to-city)
  (alive ?character - character)
  (at ?object - object ?place - place)
  (belongsto ?item - item ?character - character)
  (has ?character - character ?item - item)
  (sick ?character - character ?sickness - sickness)
  (cures ?item - item ?sickness - sickness)
  (loves ?lover - character ?love - character)
  (recovered ?p - character)
  (the-end)
)

(:action arrest
  :parameters (?s - sheriff ?p - character ?l - place)
  :actors (?s)
  :precondition (and
    (at ?s ?l)
    (at ?p ?l)
    (done-crime ?p)
    (not (arrested ?p))
    (theCriminal ?p)
    (not (criminal-arrested))
    (theArrester ?s)
  )
  :effect (and
    (arrested ?p)
    (criminal-arrested)
  ))


(:action repair-house
  :parameters (?p - character)
  :actors (?p)
  :precondition (and
    (alive ?p)
  )
  :effect (and 
    (winter-proofed-house)
  )
)


(:action prepare-for-winter
  :parameters (?p - character)
  :actors (?p)
  :precondition (and
    (autumn)
    (alive ?p)
    (winter-proofed-house)
    (has-firewood ?p)
  )
  :effect (and 
    (prepared-for-winter)
  )
)

(:action turn-into-winter
  :parameters ()
  :precondition (and
    (autumn)
    (prepared-for-winter)
  )
  :effect (and
    (not (autumn))
    (winter)
  )
)


(:action live-through-winter
  :parameters (?p ?f - character)
  :actors (?p)
  :precondition (and
    (winter)
    (family ?p ?f)
    (healthy ?f)
  )
  :effect (and 
    (not (winter))
    (spring)
  )
)

(:action survived
  :parameters (?p - rancher ?f - character)
  :actors (?p)
  :precondition (and
    (spring)
    (theFarmChar ?p)
    (alive ?p)
    (family ?p ?f)
    (alive ?f)
  )
  :effect (and 
    (survived-winter)
  )
)

(:action travel
  :parameters (?character - character ?from - place ?to - place)
  :actors (?character)
  :precondition (and 
    (not (= ?to theCity))
    (not (= ?to ?from))
    (alive ?character)
    (healthy ?character)
    (not (arrested ?character))
    (at ?character ?from)
  )
  :effect (and 
    (at ?character ?to)
    (not (at ?character ?from)))
)

(:action travel-to-city
  :parameters (?p - character ?f ?t - place)
  :actors (?p)
  :precondition (and 
    (= ?t theCity)
    (not (= ?t ?f))
    (has-ticket ?p)
    (alive ?p)
    (at ?p ?f)
    (theMover ?p)
    (decided-move-city)
  )
  :effect (and 
    (moved-to-city)
    (at ?p ?t)
    (not (at ?p ?t))
  )
)

(:action sell-land
  :parameters (?p1 - rancher ?p2 - character ?l - place)
  :actors (?p1)
  :precondition (and
    (owns ?p1 ?l)
    (wants ?p2 ?l)
    (has-cash ?p2)
    (decided-move-city)
  )
  :effect (and
    (has-cash ?p1)
    (not (has-cash ?p2))
    (owns ?p2 ?l)
    (not (owns ?p1 ?l))
  )
)

(:action decide-to-move-to-city
  :parameters (?p - rancher ?l - place)
  :actors (?p)
  :precondition (and
    (at ?p ?l)
    (theMover ?p)
  )
  :effect (and
    (decided-move-city)
  )
)
(:action buy-ticket
  :parameters (?p ?r - character ?l - place)
  :actors (?p)
  :precondition (and
    (has-cash ?p)
    (= ?r railwaydeveloper)
  )
  :effect (and
    (has-ticket ?p)
    (not (has-cash ?p))
    (has-cash ?r)
  )
)

(:action steal-cash
  :parameters (?p1 ?p2 - character ?l - place)
  :actors (?p1)
  :precondition (and
    (at ?p1 ?l)
    (at ?p2 ?l)
    (has-cash ?p2)
    (theCriminal ?p1)
    )
  :effect (and
    (has-cash ?p1)
    (not (has-cash ?p2))
    (done-crime ?p1)
    (crime-done)
  ))

(:action steal-medicine
  :parameters (?p - character ?l - place)
  :actors (?p)
  :precondition (and
    (at ?p ?l)
    (theInvalid ?p)
    (invalid-unwell)
    (not (has-cash ?p))
    )
  :effect (and
    (has-medicine ?p)
  ))


(:action steal-firewood
  :parameters (?p1 ?p2 - character)
  :actors (?p1)
  :precondition (and
    (has-firewood ?p2)
  )
  :effect (and
    (not (has-firewood ?p2))
  )
)

(:action chop-wood
  :parameters (?p - character)
  :actors (?p)
  :precondition (and
    (not (has-firewood ?p))
  )
  :effect (and
    (has-firewood ?p)
  )
)


; A character gets bitten by a rattlesnake and becomes sick.
(:action get-snake-bite
  :parameters (?v - character)
  :precondition (and
    (healthy ?v)
    (theInvalid ?v)
  )
  :effect (and 
    (not (healthy ?v))
    (invalid-unwell)
    (not (invalid-recovered))
  )
)

(:action get-medicine
  :parameters (?p ?h - character ?l - place)
  :actors (?p)
  :precondition (and
    (has-cash ?p)
    (not (has-medicine ?p))
    (has-medicine ?h)
    (at ?p ?l)
    (at ?h ?l)
  )
  :effect (and
    (has-medicine ?p)
    (not (has-cash ?p))
    (has-cash ?h)
    (not (has-medicine ?h))
  )
)

(:action heal
  :parameters (?h - rancher)
  :precondition (and 
    (has-medicine ?h)
    (not (healthy ?h))
    (theInvalid ?h)
    (invalid-unwell)
  )
  :effect (and 
    (healthy ?h)
    (not (has-medicine ?h))
    (recovered ?h)
    (not (invalid-unwell))
    (invalid-recovered)
  )
)

(:action recover
  :parameters (?p - character)
  :precondition (and 
    (not (= ?p thefarmer))
    (has-medicine ?p)
    (not (healthy ?p))
    (theInvalid ?p)
    (invalid-unwell)
  )
  :effect (and 
    (healthy ?p)
    (not (has-medicine ?p))
    (recovered ?p)
    (not (invalid-unwell))
    (invalid-recovered)
  )
)
)
