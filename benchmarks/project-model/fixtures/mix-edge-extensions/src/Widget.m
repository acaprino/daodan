#import "Widget.h"

@implementation Widget

- (NSString *)render {
    return [NSString stringWithFormat:@"<%@>", self.title];
}

@end
