(define (domain domain-basketball)

; I guess this domain can be nicer.
; we have four characters in this domain: Alice, Bob, Charlie and David.
; All three men wants Alice dead. 
; Each character can commit murder on his own or join force or frame each other.
; Once murder is commited Sherlock comes to figure out how murdered Alice.
; Each character can do the following: 
;  1- [ ] call-in-crime, 
;  2- [ ] commit murder (must have a murder weapon + be at the same place with the victim + has intention to kill).
;  3- [ ] go from one place to another.
;  4- [ ] frame another person by stealing their stuff.
;  5- [ ] follow person
; what is our intentions that we can model, kill alice + not get caught.
; 

(:requirements :adl :typing :negative-preconditions :equality)

(:types      
	character item place fact - object
	citizen - character
	police - character
	detective inspector - police
	; weapon - item
)

(:predicates
	
	(at ?object - object ?place - place)
	(alive ?character - character)
	(dead ?character - character)
	(has ?character - character ?item - item)
	(owns ?character - character ?item - item)
	(owns-place ?character - character ?place - place)
	(weapon ?weapon - item)
	(murder-weapon ?item - item)
	(murder ?murderer - character ?victim - character)
	(arressted ?character - character)
	(get-away ?character - character)
	(the-end)

	; ; (suspect ?character - character)
	
	
	; (accept-invitation ?invitee - character ?inviter - character ?place - place)
	
	; ; (invited ?character - character ?place - place)
	

	; (arrester ?p - police)
	; (arressted ?character - character)
	

	; (find-murderer ?police - police ?victim - character)
	(found-murder-weapon ?police - police ?weapon - item ?victim - character)

	(murderer-found) ; this predicate denotes if the arrestee is the murderer.
	(framed-citizen) ; this predicate denotes that the murderer escaped with their murder.
)

(:action travel 
	:parameters (?character - character ?from - place ?to - place)
	:precondition (and 
		(not (= ?from ?to))
		(at ?character ?from)
		(alive ?character)
	)
	:effect (and 
		(not (at ?character ?from))
		(at ?character ?to)
	)
)

; do we need to do so or the compilation will do it for use.
(:action kill
	:parameters (?murderer - character ?victim - character ?weapon - item ?place - place)
	:precondition (and 
		(at ?murderer ?place) 
		(at ?victim ?place)
		(alive ?murderer)
		(alive ?victim)
		(has ?murderer ?weapon)
		(weapon ?weapon)
	)
	:effect (and 
		(at ?weapon ?place)
		(murder ?murderer ?victim)
		(murder-weapon ?weapon)
		(not (alive ?victim))
		(dead ?victim)
		(when (owns ?murderer ?weapon) (arressted ?murderer))
		(when (not (owns ?murderer ?weapon)) (get-away ?murderer))
	)
)

(:action pick
	:parameters (?character - character ?item - item ?character2 - character ?place - place)
	:precondition (and 
		(at ?character ?place)
		(at ?item ?place)
		(forall (?c - character) (not (has ?c ?item)))
	)
	:effect (and 
		(has ?character ?item)
		(not (at ?item ?place))
		(when (weapon ?item) (dead ?character2))
	)
)

(:action invite
	:parameters (?inviter - character ?invitee - character ?place - place)
	:precondition (and 
		(alive ?inviter)
		(alive ?invitee)
		(not (at ?invitee ?place))
		(at ?inviter ?place)
	)
	:effect (and 
		(at ?invitee ?place)
		(when (and (dead ?invitee) (owns-place ?inviter ?place)) (arressted ?inviter))
		(when (and (dead ?invitee) (not (owns-place ?inviter ?place))) (get-away ?inviter))
	)
)

(:action call-in-crime
	:parameters (?character - character ?victim - character ?police - police ?place - place)
	:precondition (and 
		(alive ?character)
		(dead ?victim)
		(at ?character ?place)
		(at ?victim ?place)
		(not (at ?police ?place))
	)
	:effect (and
		(at ?police ?place)
	)
)

(:action find-clue
	:parameters (?police - police ?weapon - item ?victim - character ?place - place)
	:precondition (and 
		(at ?police ?place)
		(at ?weapon ?place)
		(alive ?police)
		(dead ?victim)
	)
	:effect (and
		(found-murder-weapon ?police ?weapon ?victim)
	) 
)

(:action arrest
	:parameters (?arrester - police ?arrestee - character ?victim - character ?weapon - item ?place - place)
	:precondition (and 
		(alive ?arrester)
		(alive ?arrestee)
		(at ?arrester ?place)
		; (at ?arrestee ?place)
		(found-murder-weapon ?arrester ?weapon ?victim)
		(dead ?victim)
	)
	:effect (and 
		(arressted ?arrestee)
		(when (murder ?arrestee ?victim) (and (murderer-found)))
		(when (not (murder ?arrestee ?victim)) (and (framed-citizen)))
	)
)

)
  
