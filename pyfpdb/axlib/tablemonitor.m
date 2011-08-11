
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

@implementation TMCallback

-(void)callback:(NSString*)tablename event:(NSString*)eventtype
{
}

@end

@implementation ClosedCallback

@synthesize myCB, title;

-(void)sendCB
{
	[*myCB callback: title event: @"window_destroyed"];
}

@end


@implementation TableMonitor

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

-(void)registerCallback:(TMCallback*)cb
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
	AXObserverAddNotification(observer, appRef, kAXWindowResizedNotification, (void *)self);
	err = AXObserverAddNotification(observer, appRef, kAXWindowMovedNotification, (void *)self);
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
		ClosedCallback *ccb = [[ClosedCallback alloc] init];
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

-(void)assignCCB:(ClosedCallback*)ccb
{
	ccb.myCB = &myCB;
}

@end

void axObserverCallback(AXObserverRef observer, 
						AXUIElementRef elementRef, 
						CFStringRef notification, 
						void *refcon) 
{
	if (CFStringCompare(notification,kAXUIElementDestroyedNotification,0) == 0) {
		ClosedCallback *ccb = refcon;
		[ccb sendCB];
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
	if ([obj isMemberOfClass: [ClosedCallback class]]) {
		ClosedCallback *ccb = refcon;
		ccb.title = title;
		return;
	}
	
	TableMonitor *tm = refcon;
	TMCallback *cb = tm.myCB;
	
	if (CFStringCompare(notification,kAXWindowCreatedNotification,0) == 0) {
		ClosedCallback *ccb = [[ClosedCallback alloc] init];
		[tm assignCCB: ccb];
		ccb.title = title;
		[ccb retain];
		err = AXObserverAddNotification(observer, elementRef, kAXUIElementDestroyedNotification, (void *)ccb);
		err = AXObserverAddNotification(observer, elementRef, kAXCreatedNotification, (void *)ccb);
		err = AXObserverAddNotification(observer, elementRef, kAXWindowMovedNotification, (void *)ccb);
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
	TableMonitor *tm = refcon;
	
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

	return event;
}