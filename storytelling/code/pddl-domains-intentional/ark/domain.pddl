;;;
;;; A highly simplified version of the actions in Indiana Jones and the Raiders of the Lost Ark
;;; Created by Stephen G. Ware
;;; Originally used to test the Glaive Narrative Planner
;;;
(define (domain indiana-jones-ark)
  (:requirements :adl :domain-axioms :intentionality :equality)
  (:types character place - object
          weapon - item)
  
  (:intendable
    at
    ; alive
    dead
    has
    open
  )

  (:delegatable 
    at
    ; alive
    dead
    has
    open
  )

  (:constants ark - item)
  (:predicates (open ?item - item)
               (alive ?character - character)
               (dead ?character - character)
               (armed ?character - character)
               (burried ?item - item ?place - place)
               (knows-location ?character - character ?item - item ?place - place)
               (at ?character - character ?place - place)
               (has ?character - character ?item - item)
               (is_weapon ?item - item)
               (the-end)
               )

  ;; A character travels from one place to another.
  (:action travel
  :parameters (?character - character ?from - place ?to - place)
  :actors (?character)
	:precondition (and 
	  (not (= ?from ?to))
    (alive ?character)
    (at ?character ?from)
  )
	:effect (and 
	  (not (at ?character ?from))
    (at ?character ?to)                     
  )
	
	)

  ;; A character excavates an item.
  (:action excavate
  :parameters (?character - character ?item - item ?place - place)
  :actors (?character)
	:precondition (and 
	  (alive ?character)
    (at ?character ?place)
    (burried ?item ?place)
    (knows-location ?character ?item ?place)  
  )
	:effect (and 
	  (not (burried ?item ?place))
    (has ?character ?item)
  )
  )

  ;; One character gives an item to another.
  (:action give
  :parameters (?giver - character ?item - item ?receiver - character ?place - place)
	:actors (?giver ?receiver)
  :precondition (and 
	  (not (= ?giver ?receiver))
    (alive ?giver)
    (at ?giver ?place)
    (has ?giver ?item)
    (alive ?receiver)
    (at ?receiver ?place)
  )
	:effect (and 
	  (not (has ?giver ?item))
    (has ?receiver ?item)
    (when (is_weapon ?item) (armed ?receiver))
  )
  )

  ;; One character kills another.
  (:action kill
    :parameters (?killer - character ?weapon - weapon ?victim - character ?place - place)
    :actors (?killer)
    :precondition (and
      (alive ?killer)
      (at ?killer ?place)
      (has ?killer ?weapon)
      (alive ?victim)
      (at ?victim ?place)
      (not (= ?killer ?victim))
    )
    :effect (and 
      (not (alive ?victim))
      (dead ?victim)
    )
    )
  
  ;; One character takes an item from another at weapon-point.
  (:action take
  :parameters (?taker - character ?item - item ?victim - character ?place - place)
  :actors (?taker)
	:precondition (and 
	  (not (= ?taker ?victim))
    (alive ?taker)
    (at ?taker ?place)
    (or 
        (dead ?victim)
        (and (armed ?taker) (not (armed ?victim)))
    )
    (at ?victim ?place)
    (has ?victim ?item)  
  )
	:effect (and 
	  (not (has ?victim ?item))
    (has ?taker ?item)
    (when (is_weapon ?item) (armed ?taker))
  )
  )

  ;; A character opens the Ark.
  (:action open-ark
  :parameters (?character - character ?l - place)
	:actors (?character)
  :precondition (and 
	  (alive ?character)
    (has ?character ark)
    (at ?character ?l)
    (knows-location ?character ark ?l)
  )
	:effect (and 
	  (open ark)
    (not (alive ?character))
    (dead ?character)
  )
  )

  ;; The Ark closes.
  (:action close-ark
  :parameters ()
	:precondition (and 
	  (open ark)
	)
	:effect (and
	  (not (open ark))
	)
	)

  ; ;; When a character has a weapon, they are armed.
  ; (:axiom
  ;   :vars    (?character - character)
  ;   :context (and (not (armed ?character))
  ;                 (exists (?w - weapon)
  ;                         (has ?character ?w)))
  ;   :implies (armed ?character))

  ; ;; When a character does not have a weapon, they are unarmed.
  ; (:axiom
  ;   :vars    (?character - character)
  ;   :context (and (armed ?character)
  ;                 (forall (?w - weapon)
  ;                         (not (has ?character ?w))))
  ;   :implies (not (armed ?character)))
  
  )