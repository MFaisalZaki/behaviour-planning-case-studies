;;;
;;; A domain for modeling stories in a magical kingdom
;;; Created by Stephen G. Ware
;;; Originally used for validating CPOCL narrative structure
;;;
(define (domain fantasy)
  (:requirements :adl :intentionality)
  (:types ; Person and monster are a types of character.
		  character item - object
          person monster - character
		  ; Items exist.
          valuable - item
		  ; Places exist.
		  place)
  (:intendable
  	alive
  	rich
  	happy
  	has
  	hungry
  )

  (:delegatable
  	alive
  	rich
  	happy
  )
  
  (:predicates ; A character is alive.
               (alive ?character - character)
			   ; A person is single.
			   (single ?person - person)
			   ; A character is rich.
               (rich ?character - character)
			   ; A character is happy.
               (happy ?character - character)
			   ; A character is hungry.
			   (hungry ?character - character)
               ; An object is at a place.
			   (at ?object - object ?place - place)
			   ; A character has an item.
			   (has ?character - character ?item - item)
			   ; An item belongs to a character
			   (belongsto ?item - item ?character - character)
			   ; One character loves another.
			   (loves ?lover - character ?love - character)
			   ; One person has proposed to another.
			   (hasproposed ?proposer - person ?proposee - person)
			   ; One person has accepted another's proposal.
			   (hasaccepted ?person1 - person ?person2 - person)
			   ; Two people are married.
			   (marriedto ?person1 - person ?person2 - person)
			   (the-end)
			   )

  ;; A character travels from one place to another.
  (:action travel
    :parameters   (?character - character ?from - place ?to - place)
    :actors       (?character)
    :precondition (and (alive ?character)
					   (at ?character ?from))
    :effect       (and (at ?character ?to)
                       (not (at ?character ?from)))
    )

  ;; One person proposes to another.
  (:action propose
    :parameters   (?proposer - person ?proposee - person ?place - place)
	:actors       (?proposer)
    :precondition (and (alive ?proposer)
	                   (at ?proposer ?place)
					   (alive ?proposee)
					   (at ?proposee ?place)
					   (loves ?proposer ?proposee))
	:effect       (hasproposed ?proposer ?proposee)
	)

  ;; One person accepts another's proposal.
  (:action accept
    :parameters   (?accepter - person ?proposer - person ?place - place)
	:actors       (?accepter)
    :precondition (and (alive ?accepter)
	                   (at ?accepter ?place)
					   (alive ?proposer)
					   (at ?proposer ?place)
					   (hasproposed ?proposer ?accepter))
	:effect       (hasaccepted ?accepter ?proposer)
	)

  ;; Two people marry.
  (:action marry
    :parameters   (?groom - person ?bride - person ?place - place)
    :actors       (?groom ?bride)
	:precondition (and (alive ?groom)
	                   (at ?groom ?place)
					   (hasproposed ?groom ?bride)
					   (single ?groom)
					   (alive ?bride)
					   (at ?bride ?place)
					   (hasaccepted ?bride ?groom)
					   (single ?bride))
	:effect       (and (marriedto ?groom ?bride)
					   (marriedto ?bride ?groom)
					   (not (single ?groom))
					   (not (single ?bride))
	                   (forall (?v - valuable)
					           (when (has ?groom ?v)
							         (rich ?bride)))
					   (when (loves ?groom ?bride)
					         (happy ?groom))
					   (when (loves ?bride ?groom)
					         (happy ?bride)))
	)

  ;; A character steals an object from another character.
  (:action steal
    :parameters   (?thief - character ?victim - character ?item - item ?place - place)
	:actors       (?thief)
    :precondition (and (not (= ?thief ?victim))
	                   (alive ?thief)
	                   (at ?thief ?place)
					   (at ?item ?place)
					   (belongsto ?item ?victim))
	:effect       (and (has ?thief ?item)
	                   (when (at ?victim ?place)
					         (intends ?victim (has ?victim ?item)))
					   (when (forall (?v - valuable)
                                     (not (has ?victim ?v)))
					         (not (rich ?victim))))
	)

  ;; A character becomes hungry.
  (:action get-hungry
    :parameters   (?character - character)
	:actors       (?character)
    :precondition (not (hungry ?character))
	:effect       (and (hungry ?character)
					   (intends ?character (not (hungry ?character))))
	)

  ;; A monster eats another character.
  (:action eat
    :parameters   (?monster - monster ?character - character ?place - place)
    :actors       (?monster)
	:precondition (and (alive ?monster)
	                   (at ?monster ?place)
					   (hungry ?monster)
					   (alive ?character)
					   (at ?character ?place))
	:effect       (and (not (hungry ?monster))
	                   (not (alive ?character))
					   (not (rich ?character))
					   (not (happy ?character)))
	)

)