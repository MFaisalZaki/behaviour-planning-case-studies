
(define (domain aladdin-story)
  (:requirements :strips :typing :equality)

  (:types character thing place fact - object
	  king knight thief monster - character
	  genie - monster
	  magic-lamp - thing)

  (:intendable
    married-to
    loves
    controls
    has
    dead
    at
  )

  (:delegatable 
    loves
    has
    dead
    at
  )

  (:constants
    ;; the cast
   jafar - king
   aladdin - knight
   jasmine - character
   dragon - monster
   gene - genie
  )

  (:predicates
   ;; basic character states
   (alive ?who - character)
   (dead ?who - character)
   (at ?who - character ?where - place)
   (unconfined ?who - character)
   (has ?who - character ?what - thing)

   (was-stolen-from ?who - character ?what - thing)
   (values-more-than ?who - character ?what-more - thing ?what-less - thing)

   ;; states specific to characters
   (loves ?who - character ?who-else - character)
   (single ?who - character)
   (married ?who - character)
   (married-to ?who - character ?who-else - character)
   (loyal-to ?king - king ?knight - knight)
   (beautiful ?who - character)

   ;; states specific to monsters
   (scary ?who - monster)
   ;; any character can control a genie; only genies can be controlled
   (controls ?who - character ?gen - genie)
   ;; only genies can inhabit lamps
   (in ?gen - genie ?lamp - magic-lamp)
   (the-end)
   )

  (:action travel
   :parameters (?traveller - character ?from - place ?dest - place)
   :actors (?traveller)
   :precondition (and 
          (alive ?traveller)
		      (at ?traveller ?from)
		      (unconfined ?traveller)
		      (not (= ?from ?dest)))
   :effect (and (not (at ?traveller ?from))
		(at ?traveller ?dest))
   )

  (:action slay
   :parameters (?slayer - knight ?slayee - monster ?where - place)
   :actors (?slayer)
   :precondition (and (at ?slayer ?where)
  		      (at ?slayee ?where)
  		      (alive ?slayer)
  		      (alive ?slayee))
   :effect (and (not (alive ?slayee))
  		(dead ?slayee))
   )

  (:action pillage
   :parameters (?pillager - character ?body - character ?what - thing
			  ?where - place)
   :actors (?pillager)
   :precondition (and (at ?pillager ?where)
		      (at ?body ?where)
		      (alive ?pillager)
		      (dead ?body)
		      (has ?body ?what))
   :effect (and (not (has ?body ?what))
		(has ?pillager ?what))
   )

  (:action steal
   :parameters (?thief - thief ?victim - character ?what - thing
		       ?where - place)
   :actors (?thief)
   :precondition (and (at ?thief ?where)
		      (at ?victim ?where)
		      (alive ?thief)
		      (has ?victim ?what))
   :effect (and (not (has ?victim ?what))
		(has ?thief ?what)
		(was-stolen-from ?victim ?what))
   )

  (:action give
   :parameters (?giver - character ?givee - character ?what - thing
		       ?where - place)
   :actors (?giver)
   :precondition (and (at ?giver ?where)
		      (at ?givee ?where)
		      (alive ?giver)
		      (alive ?givee)
		      (has ?giver ?what)
		      (not (= ?giver ?givee)))
   :effect (and (not (has ?giver ?what))
		(has ?givee ?what))
   )

  (:action trade
   :parameters (?trader1 - character ?trader2 - character
			 ?what1 - thing ?what2 - thing ?where - place)
   :actors (?trader1)
   :precondition (and (at ?trader1 ?where)
		      (at ?trader2 ?where)
		      (alive ?trader1)
		      (alive ?trader2)
		      (has ?trader1 ?what1)
		      (has ?trader2 ?what2)
		      (not (values-more-than ?trader1 ?what1 ?what2))
		      (values-more-than ?trader2 ?what1 ?what2)
		      (not (= ?trader1 ?trader2)))
   :effect (and (not (has ?trader1 ?what1))
		(not (has ?trader2 ?what2))
		(has ?trader2 ?what1)
		(has ?trader1 ?what2))
   )

  (:action summon
   :parameters (?who - character ?gen - genie ?lamp - magic-lamp
		     ?where - place)
   :actors (?who)
   :precondition (and (at ?who ?where)
		      (has ?who ?lamp)
		      (alive ?who)
		      (in ?gen ?lamp)
		      (alive ?gen)
		      (not (= ?who ?gen)))
   :effect (and (not (in ?gen ?lamp))
		(at ?gen ?where)
		(unconfined ?gen)
		(controls ?who ?gen))
   )

  (:action love-spell
   :parameters (?gen - genie ?target - character ?lover - character ?lamp - magic-lamp)
   :actors (?gen)
   :precondition (and (unconfined ?gen)
		      (alive ?gen)
		      (alive ?target)
		      (alive ?lover)
		      (has ?lover ?lamp)
		      (not (= ?gen ?target))
		      (not (= ?gen ?lover))
		      (not (= ?target ?lover)))
   :effect (and (loves ?target ?lover)
		(intends ?target (married-to ?target ?lover)))
   )

  (:action marry
   :parameters (?groom - character ?bride - character ?where - place)
   :actors (?groom ?bride)
   :precondition (and (at ?groom ?where)
		      (at ?bride ?where)
		      (alive ?groom)
		      (alive ?bride)
		      (loves ?groom ?bride)
		      (loves ?bride ?groom)
		      (single ?groom)
		      (single ?bride))
   :effect (and (not (single ?groom))
		(married ?groom)
		(not (single ?bride))
		(married ?bride)
		(married-to ?groom ?bride)
		(married-to ?bride ?groom))
   )

  (:action order
   :parameters (?king - king ?knight - knight ?where - place
		      ?objective - fact)
   :actors (?king)
   :precondition (and (at ?king ?where)
		      (at ?knight ?where)
		      (alive ?king)
		      (alive ?knight)
		      (loyal-to ?king ?knight))
   :effect (and (intends ?knight ?objective))
   )

  ;; (:action persuade
  ;;  :parameters (?who - character ?who-else - character ?where - place
  ;; 		     ?objective - fact)
  ;;  :actors (?who)
  ;;  :precondition (and (at ?who ?where)
  ;; 		      (at ?who-else ?where)
  ;; 		      (alive ?who)
  ;; 		      (alive ?who-else)
  ;; 		      (loves ?who-else ?who))
  ;;  :effect (and (intends ?who-else ?objective))
  ;;  )

  (:action command
   :parameters (?who - character ?gen - genie ?lamp - magic-lamp ?objective - fact)
   :actors (?who)
   :precondition (and (alive ?who)
		      (alive ?gen)
		      (has ?who ?lamp)
		      (controls ?who ?gen)
		      (not (= ?who ?gen)))
   :effect (and (intends ?gen ?objective))
   )

  (:action fall-in-love
   :parameters (?who - character ?with-who - character ?where - place)
   :precondition (and (at ?who ?where)
		      (at ?with-who ?where)
		      (not (= ?who ?with-who))
		      (alive ?who)
		      (single ?who)
		      (alive ?with-who)
		      ; (beautiful ?with-who)
		      (not (loves ?with-who ?who))
		    )
   :effect (and (loves ?who ?with-who)
		(intends ?who (married-to ?who ?with-who)))
   )

  (:action frighten
   :parameters (?frighter - monster ?frightee - character ?where - place)
   :precondition (and (at ?frighter ?where)
		      (at ?frightee ?where)
		      (alive ?frighter)
		      (scary ?frighter)
		      (alive ?frightee)
		      (not (= ?frighter ?frightee)))
   :effect (and (intends ?frightee (dead ?frighter)))
   )
  


  )
