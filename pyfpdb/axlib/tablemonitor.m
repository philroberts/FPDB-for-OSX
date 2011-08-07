
#import "tablemonitor.h"

void axObserverCallback(AXObserverRef observer, 
						AXUIElementRef elementRef, 
						CFStringRef notification, 
						void *refcon);	

CGEventRef myEventTapCallBack (
							   CGEventTapProxy proxy,
							   CGEventType type,
							   CGEventRef event,
							   void *refcon
							   );

@implementation tmcallback

-(void)callback:(NSString*)tablename event:(NSString*)eventtype
{
}

@end

@implementation closedcallback

@synthesize myCB, title;

-(void)sendCB
{
	[*myCB callback: title event: @"window_destroyed"];
}

@end


@implementation tablemonitor

@synthesize appRef, appPID, myCB;

-(void)detectFakePS
{
	NSWorkspace * ws = [NSWorkspace sharedWorkspace];
	NSArray *apps = [ws launchedApplications];
	BOOL found = FALSE;
	for (id app in apps) {
		if ([[app objectForKey:@"NSApplicationName"] isEqualToString: @"Python"]) {
			appPID =(pid_t) [[app objectForKey:@"NSApplicationProcessIdentifier"] intValue];
			appRef = AXUIElementCreateApplication(appPID);
			CFRetain(appRef);
			
			NSArray *children;
			AXError err = AXUIElementCopyAttributeValues(appRef, kAXChildrenAttribute, 0, 100, (CFArrayRef *)&children);
			CFMakeCollectable(children);
			
			if (err != kAXErrorSuccess) {
				return;
			}
			
			for (id child in children) {
				NSString *title;
				AXUIElementCopyAttributeValue((AXUIElementRef)child,kAXTitleAttribute,(CFTypeRef *)&title);
				if (err != kAXErrorSuccess) {
					return;
				}
				CFMakeCollectable(title);
				if ([title isEqualToString:@"Meeus"]) {
					found = TRUE;
					break;
				}
			}
			if (!found) {
				CFRelease(appRef);
			}
		}
		if (found) {
			break;
		}
	}
	return;
}

-(void)detectPS
{
	NSWorkspace * ws = [NSWorkspace sharedWorkspace];
	NSArray *apps = [ws launchedApplications];
	for (id app in apps) {
		if ([[app objectForKey:@"NSApplicationName"] isEqualToString: @"PokerStars"]) {
			appPID =(pid_t) [[app objectForKey:@"NSApplicationProcessIdentifier"] intValue];
			appRef = AXUIElementCreateApplication(appPID);
			CFRetain(appRef);
		}
	}
	return;
}

-(void)registerCallback:(tmcallback*)cb
{
	myCB = cb;
}

-(void)runCallback
{
	[myCB callback:@"Notable" event:@"Noevent"];
}

-(void)runCallback:(NSString*)table event:(NSString*)eventtype
{
	[myCB callback:table event:eventtype];
}

-(void)runCallback:(NSString*)msg
{
	fprintf(stdout, "%s\n", [msg cString]);
	[self runCallback];
}

-(void)doObserver
{
	AXError err = AXObserverCreate(appPID, axObserverCallback, &observer);
	
	if (err != kAXErrorSuccess) {
		fprintf(stderr, "AXObserverCreate failed\n");
		[[NSApplication sharedApplication] terminate: nil];			
	}
	
	err = AXObserverAddNotification(observer, appRef, kAXWindowCreatedNotification, (void *)self);
	fprintf(stderr, "err: %d\n", err);
	AXObserverAddNotification(observer, appRef, kAXWindowResizedNotification, (void *)self);
	err = AXObserverAddNotification(observer, appRef, kAXWindowMovedNotification, (void *)self);
	fprintf(stderr, "err: %d\n", err);
	AXObserverAddNotification(observer, appRef, kAXFocusedWindowChangedNotification, (void *)self);
	AXObserverAddNotification(observer, appRef, kAXApplicationActivatedNotification, (void *)self);
	AXObserverAddNotification(observer, appRef, kAXApplicationDeactivatedNotification, (void *)self);

	CFRunLoopAddSource ([[NSRunLoop currentRunLoop] getCFRunLoop], AXObserverGetRunLoopSource(observer), kCFRunLoopDefaultMode);
	
	NSArray *children;
	err = AXUIElementCopyAttributeValues(appRef, kAXChildrenAttribute, 0, 100, (CFArrayRef *)&children);
	CFMakeCollectable(children);
	
	if (err != kAXErrorSuccess) {
		return;
	}
	
	for (id child in children) {
		NSString *title;
		AXUIElementCopyAttributeValue((AXUIElementRef)child,kAXTitleAttribute,(CFTypeRef *)&title);
		if (err != kAXErrorSuccess) {
			return;
		}
		CFMakeCollectable(title);
		closedcallback *ccb = [[closedcallback alloc] init];
		ccb.myCB = &myCB;
		ccb.title = title;
		[ccb retain];
		AXObserverAddNotification(observer, (AXUIElementRef)child, kAXUIElementDestroyedNotification, (void *)ccb);
	}
	
	ProcessSerialNumber psn;
	GetProcessForPID(appPID, &psn);
	CFMachPortRef tap = CGEventTapCreateForPSN (&psn,
												kCGTailAppendEventTap,
												kCGEventTapOptionListenOnly,
												CGEventMaskBit(kCGEventLeftMouseDown),
												myEventTapCallBack,
												(void *)self);
	CFMachPortCreateRunLoopSource(NULL, tap, 0);
	CFRunLoopAddSource ([[NSRunLoop currentRunLoop] getCFRunLoop], CFMachPortCreateRunLoopSource(NULL, tap, 0), kCFRunLoopDefaultMode);
}

-(void)assignCCB:(closedcallback*)ccb
{
	ccb.myCB = &myCB;
}

@end

void axObserverCallback(AXObserverRef observer, 
						AXUIElementRef elementRef, 
						CFStringRef notification, 
						void *refcon) 
{
	NSString *tempstr = notification;
	fprintf(stdout, "notification: %s\n", [tempstr cString]);
	if (CFStringCompare(notification,kAXUIElementDestroyedNotification,0) == 0) {
		closedcallback *ccb = refcon;
		fprintf(stdout, "In dest callback\n");
		[ccb sendCB];
		fprintf(stdout, "Sent cb\n");
		[ccb release];
		return;
	}

	NSString *title;
	AXError err = AXUIElementCopyAttributeValue(elementRef,kAXTitleAttribute,(CFTypeRef *)&title);
	if (err != kAXErrorSuccess) {
		return;
	}
	CFMakeCollectable(title);
	
	NSObject *obj = refcon;
	if ([obj isMemberOfClass: [closedcallback class]]) {  //CFStringCompare(notification, CFSTR("AXTitleChanged"), 0) == 0) {
		fprintf(stdout, "Title changed to %s?\n", [title cString]);
		closedcallback *ccb = refcon;
		ccb.title = title;
		return;
	}
	
	tablemonitor *tm = refcon;
	tmcallback *cb = tm.myCB;
	
	if (CFStringCompare(notification,kAXWindowCreatedNotification,0) == 0) {
		closedcallback *ccb = [[closedcallback alloc] init];
		//ccb.myCB = tm.myCB;
		[tm assignCCB: ccb];
		ccb.title = title;
		[ccb retain];
		err = AXObserverAddNotification(observer, elementRef, kAXUIElementDestroyedNotification, (void *)ccb);
		err = AXObserverAddNotification(observer, elementRef, kAXCreatedNotification, (void *)ccb);
		err = AXObserverAddNotification(observer, elementRef, kAXWindowMovedNotification, (void *)ccb);
		//err = AXObserverAddNotification(observer, elementRef, CFSTR("AXTitleChanged"), (void *)ccb); // DOESN'T WORK ON POKERSTARS QQ
		fprintf(stdout, "add err: %d\n", err);
//		[cb callback:title event:@"window_created"];
	} else if (CFStringCompare(notification,kAXWindowResizedNotification,0) == 0) {
		[cb callback:title event:@"window_resized"];
	} else if (CFStringCompare(notification,kAXApplicationActivatedNotification,0) == 0) {
		// For some reason, this and the next notification get called multiple times.  
		[cb callback:title event:@"app_activated"];
	} else if (CFStringCompare(notification,kAXApplicationDeactivatedNotification,0) == 0) {
		[cb callback:title event:@"app_deactivated"];
	} else if (CFStringCompare(notification,kAXFocusedWindowChangedNotification,0) == 0) {
		[cb callback:title event:@"focus_changed"];
	} else if (CFStringCompare(notification,kAXWindowMovedNotification,0) == 0) {
		[cb callback:title event:@"window_moved"];
	} else if (CFStringCompare(notification, kAXValueChangedNotification, 0) == 0) {
		[cb callback:title event:@"value_changed"];
	}
}

CGEventRef myEventTapCallBack (
							   CGEventTapProxy proxy,
							   CGEventType type,
							   CGEventRef event,
							   void *refcon
							   )
{
	tablemonitor *tm = refcon;
	
	NSArray *children;
	AXError err = AXUIElementCopyAttributeValues(tm.appRef, kAXChildrenAttribute, 0, 100, (CFArrayRef *)&children);
	CFMakeCollectable(children);
	
	if (err != kAXErrorSuccess) {
		return event;
	}
	
	for (id child in children) {
		NSString *value;
		AXUIElementCopyAttributeValue((AXUIElementRef)child,kAXMainAttribute,(CFTypeRef *)&value);	
		// Check to see if this is main window we're looking at.  It's here that we'll send the mouse events.
		if ([value intValue] == 1) {
			NSString *title;
			AXUIElementCopyAttributeValue((AXUIElementRef)child,kAXTitleAttribute,(CFTypeRef *)&title);
			CFMakeCollectable(title);
			[tm.myCB callback:title event:@"clicked"];
			return event;
		}
	}
	
	switch (type) {
			/* The null event. */
		case kCGEventNull:
			fprintf(stdout, "Null event\n");
			break;
			/* Mouse events. */
		case kCGEventLeftMouseDown:
			fprintf(stdout, "leftmousedown event\n");
			break;
		case kCGEventLeftMouseUp:
			fprintf(stdout, "leftmouseup event\n");
			break;
		case kCGEventRightMouseDown:
			fprintf(stdout, "rightmousedown event\n");
			break;
		case kCGEventRightMouseUp:
			fprintf(stdout, "rightmouseup event\n");
			break;
		case kCGEventMouseMoved:
			fprintf(stdout, "mousemoved event\n");
			break;
		case kCGEventLeftMouseDragged:
			fprintf(stdout, "leftmousedragged event\n");
			break;
		case kCGEventRightMouseDragged:
			fprintf(stdout, "rightmousedragged event\n");
			break;
			/* Keyboard */
		case kCGEventKeyDown:
			fprintf(stdout, "keydown event\n");
			break;
		case kCGEventKeyUp:
			fprintf(stdout, "keyup event\n");
			break;
		case kCGEventFlagsChanged:
			fprintf(stdout, "eventflagschanged event\n");
			break;
			/* Specialised control devices */
		case kCGEventScrollWheel:
			fprintf(stdout, "scrollwheel event\n");
			break;
		case kCGEventTabletPointer:
			fprintf(stdout, "tabletpointer event\n");
			break;
		case kCGEventTabletProximity:
			fprintf(stdout, "tabletproximity event\n");
			break;
		case kCGEventOtherMouseDown:
			fprintf(stdout, "othermousedown event\n");
			break;
		case kCGEventOtherMouseUp:
			fprintf(stdout, "othermouseup event\n");
			break;
		case kCGEventOtherMouseDragged:
			fprintf(stdout, "othermousedragged event\n");
			break;
			/* Out of band event types. These are delivered to the event tap callback
			 to notify it of unusual conditions that disable the event tap. */
		case kCGEventTapDisabledByTimeout:
			fprintf(stdout, "tapdisabledtimeout event\n");
			break;
		case kCGEventTapDisabledByUserInput:
			fprintf(stdout, "tapdisableduser event\n");
			break;
		default:
			fprintf(stdout, "unknown event\n");
			break;
	}
	return event;
}