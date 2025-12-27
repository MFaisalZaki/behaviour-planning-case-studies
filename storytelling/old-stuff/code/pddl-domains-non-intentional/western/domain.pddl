;;;
;;; A domain for modeling stories in the Wild West
;;; Created by Stephen G. Ware
;;; Originally used for validating CPOCL narrative structure
;;;
(define (domain western)
  (:requirements :adl)
  (:types ; People and animals are living things.
          living place item - object
          character animal - living
          ; Animals are items that can be owned.
          ; Some items are valuable.
          valuable - item
          ; Sicknesses exist
          sickness)

  (:constants ; A place to imprison criminals
              jailhouse - place
              ; The "sickness" of being bitten by a poisonous snake
              snakebite - sickness)
  (:predicates ; A character is alive.
               (alive ?character - character)
               (dead ?character - character)
               ; A character is not restrained.
               (free ?character - character)
               (restrained ?character - character)
               ; A character is the sheriff.
               (sheriff ?character - character)
               ; A character or thing is at a place.
               (at ?object - object ?place - place)
               ; An item belongs to a character.
               (belongsto ?item - item ?character - character)
               ; A character has an item.
               (has ?living - living ?object - object)
               ; A character is sick with some kind of sickness.
               (sick ?character - character ?sickness - sickness)
               (healed ?character - character ?sickness - sickness)
               ; An item can cure a sickness.
               (cures ?item - item ?sickness - sickness)
               ; One character loves another.
               (loves ?lover - character ?love - character)
               (the-end)
               )

  ; A character gets bitten by a rattlesnake and becomes sick.
  (:action snakebite_action
    :parameters   (?victim - character ?lover - character)
    :precondition (and (alive ?victim))
    :effect       (and (sick ?victim snakebite)
                      (healed ?victim snakebite)
                      (when (loves ?lover ?victim)
                            (and 
                              (not (sick ?victim snakebite))
                              (healed ?victim snakebite)
                            ))
                       ))

  ; A character dies of dies of some sickness.
  (:action die
    :parameters   (?character - character ?sickness - sickness)
    :precondition (and (alive ?character)
                       (sick ?character ?sickness))
    :effect       (and (dead ?character) (not (alive ?character))))

  ; A character travels from one location to another.
  (:action travel
    :parameters   (?character - character ?from - place ?to - place)
    :precondition (and (alive ?character)
                       (free ?character)
                       (at ?character ?from))
    :effect       (and (at ?character ?to)
                       (not (at ?character ?from)))
    )

  ; A character forces a tied up character to move from one place to another.
  (:action forcetravel
    :parameters   (?character - character ?victim - character ?from - place ?to - place)
    :precondition (and (alive ?character)
                       (free ?character)
                       (at ?character ?from)
                       (alive ?victim)
                       (not (free ?victim))
                       (restrained ?victim)
                       (at ?victim ?from))
    :effect       (and (at ?character ?to)
                       (not (at ?character ?from))
                       (at ?victim ?to)
                       (not (at ?victim ?from)))
    )

  ; One character gives an item to another.
  (:action give
    :parameters   (?giver - character ?receiver - character ?item - item ?place - place)
    :precondition (and (alive ?giver)
                       (free ?giver)
                       (at ?giver ?place)
                       (has ?giver ?item)
                       (alive ?receiver)
                       (free ?receiver)
                       (at ?receiver ?place))
    :effect       (and (has ?receiver ?item)
                       (not (has ?giver ?item))
                       (when (belongsto ?item ?giver)
                             (belongsto ?item ?receiver)))
    )

  ; One character ties up another.
  (:action tieup
    :parameters   (?character - character ?victim - character ?place - place)
    :precondition (and 
      (not (= ?character ?victim))
      (alive ?character)
                       (free ?character)
                       (at ?character ?place)
                       (alive ?victim)
                       (at ?victim ?place))
    :effect       (and (not (free ?victim))
                       (restrained ?victim)
                       (free ?victim)
                       
                       )
    )

  ; One character unties another.
  (:action untie
    :parameters   (?character - character ?victim - character ?place - place)
    :precondition (and (alive ?character)
                       (free ?character)
                       (at ?character ?place)
                       (alive ?victim)
                       (not (free ?victim))
                       (restrained ?victim)
                       (at ?victim ?place))
    :effect       (free ?victim)
    )

  ; One character takes an item from a tied up character.
  (:action take
    :parameters   (?taker - character ?item - item ?victim - character ?place - place)
    :precondition (and (not (= ?taker ?victim))
                       (alive ?taker)
                       (free ?taker)
                       (at ?taker ?place)
                       (alive ?victim)
                       (not (free ?victim))
                       (restrained ?victim)
                       (at ?victim ?place)
                       (has ?victim ?item)
                  )
    :effect       (and (has ?taker ?item)
                       (not (has ?victim ?item))
                       (when (belongsto ?item ?victim)
                             (and (has ?victim ?item)
                                  
                                  )))
    )

  (:action arrest
      :parameters (?s - character ?taker - character ?victim - character ?item - item ?place - place)
      :precondition (and
        (not (= ?taker ?victim))
        (alive ?taker)
        (free ?taker)
        (at ?taker ?place)
        (alive ?victim)
        (not (free ?victim))
        (restrained ?victim)
        (at ?victim ?place)
        (has ?victim ?item)
        (sheriff ?s)
      )
      :effect (and 
        (at ?taker jailhouse)
        (not (free ?taker))
        (restrained ?taker)
        (has ?victim ?item)
        (free ?victim)
      )
  )
  
  ; One character uses medicine to heal a sick character.
  (:action heal
    :parameters   (?healer - character ?patient - character ?sickness - sickness ?medicine - item ?place - place)
    :precondition (and (cures ?medicine ?sickness)
                       (alive ?healer)
                       (free ?healer)
                       (at ?healer ?place)
                       (has ?healer ?medicine)
                       (alive ?patient)
                       (at ?patient ?place)
                       (sick ?patient ?sickness))
    :effect       (and (not (sick ?patient ?sickness))
                       (healed ?patient ?sickness)
                       (not (has ?healer ?medicine)))
    )
)